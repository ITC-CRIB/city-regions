import os
import numpy as np
import rasterio
from pyproj import Transformer, Geod
from shapely import geometry

from tqdm.auto import tqdm

def regrid(path, dataset_name, template_name, row0 = 0, row1 = None, virtual_points=4):

    assert virtual_points >= 3, "Number of virtual points should be larger than 3"

    dataset = rasterio.open(os.path.join(path, dataset_name))
    print("Source raster:")
    print(f"  Width: {dataset.width}, Height: {dataset.height}")
    print(f"  Pixel size: {dataset.res}")
    print(f"  Bounds: {dataset.bounds}")
    print(f"  CRS: {dataset.crs}")
    print(f"  Data type: {dataset.dtypes[0]}")
    print(f"  No data: {dataset.nodata}")

    template = rasterio.open(os.path.join(path, template_name))
    print("Template raster:")
    print(f"  Width: {template.width}, Height: {template.height}")
    print(f"  Pixel size: {template.res}")
    print(f"  Bounds: {template.bounds}")
    print(f"  CRS: {template.crs}")
    print(f"  Data type: {template.dtypes[0]}")
    print(f"  No data: {template.nodata}")

    if not row1 or row1 > dataset.height:
        row1 = dataset.height

    transformer = Transformer.from_crs(dataset.crs, template.crs, always_xy=True)
    print(transformer)

    geod = Geod(ellps="WGS84")
    print(geod)

    assert row1 >= row0, "End row should be larger than the start row"

    print(f"Processing rows {row0}-{row1}")

    data = dataset.read(1)

    t_data = np.full((template.height, template.width), -1, dtype=np.float32)
    t_nodata = t_data[0][0]

    skip = 0
    skip_val = 0.0
    
    for row in tqdm(range(row0, row1)):
        for col in range(dataset.width):
            val = data[row, col]

            if val == dataset.nodata:
                continue

            x0, y0 = dataset.xy(row, col, offset="ul")
            x1, y1 = dataset.xy(row, col, offset="lr")

            points = [(x, y0) for x in np.linspace(x0, x1, virtual_points)]
            points += [(x1, y) for y in np.linspace(y0, y1, virtual_points)][1:]
            points += [(x, y1) for x in np.linspace(x1, x0, virtual_points)][1:]
            points += [(x0, y) for y in np.linspace(y1, y0, virtual_points)][1:]

            t_points = list(transformer.itransform(points, errcheck=True))
            polygon = geometry.Polygon(t_points)
            area, _ = geod.geometry_area_perimeter(polygon)

            try:
                t_x0, t_y0, t_x1, t_y1 = polygon.bounds
                t_row0, t_col0 = template.index(t_x0, t_y0)
                t_row1, t_col1 = template.index(t_x1, t_y1)
            except:
                print(f"Invalid polygon bounds {row}:{col}, {val}")
                skip += 1
                skip_val += val
                continue
                
            if t_row0 > t_row1:
                t_row0, t_row1 = t_row1, t_row0
            if t_col0 > t_col1:
                t_col0, t_col1 = t_col1, t_col0

            for t_row in range(t_row0, t_row1 + 1):
                for t_col in range(t_col0, t_col1 + 1):
                    t_x0, t_y0 = template.xy(t_row, t_col, offset="ul")
                    t_x1, t_y1 = template.xy(t_row, t_col, offset="lr")

                    c_points = [(x, t_y0) for x in np.linspace(t_x0, t_x1, virtual_points)]
                    c_points += [(t_x1, y) for y in np.linspace(t_y0, t_y1, virtual_points)][1:]
                    c_points += [(x, t_y1) for x in np.linspace(t_x1, t_x0, virtual_points)][1:]
                    c_points += [(t_x0, y) for y in np.linspace(t_y1, t_y0, virtual_points)][1:]

                    cell = geometry.Polygon(c_points)

                    if cell.intersects(polygon):
                        part = cell.intersection(polygon)
                        part_area, _ = geod.geometry_area_perimeter(part)
                        part_ratio = part_area / area
                        part_val = val * part_ratio

                        if t_data[t_row][t_col] == t_nodata:
                            t_data[t_row][t_col] = part_val
                        else:
                            t_data[t_row][t_col] += part_val

    if skip:
        print(f"{skip} cells skipped, {skip_val} population.")
        
    with rasterio.open(
        os.path.join(path, f"grid-{row0}-{row1}.tif"),
        'w',
        driver='GTiff',
        height=t_data.shape[0],
        width=t_data.shape[1],
        count=1,
        dtype=np.float32,
        crs=template.crs,
        transform=template.transform,
        nodata=t_nodata,
        compress='deflate'
    ) as grid:
        grid.write(t_data, 1)
    grid.close()

    dataset.close()
    template.close()

    t_data = None
    data = None


path = os.environ.get('REGRID_PATH')
assert path, "No path"

dataset = os.environ.get('REGRID_DATASET')
assert dataset, "No input dataset"

template = os.environ.get('REGRID_TEMPLATE')
assert template, "No template dataset"

row_start = int(os.environ.get('REGRID_ROW_START', 0))
row_end = int(os.environ.get('REGRID_ROW_END'))

row_delta = int(os.environ.get('REGRID_ROW_DELTA', 100))
assert row_delta, "Invalid row delta"

virtual_points = int(os.environ.get('REGRID_VIRTUAL_POINTS', 4))

for row0 in range(row_start, row_end, row_delta):
    row1 = row0 + row_delta
    if not os.path.exists(os.path.join(path, f"grid-{row0}-{row1}.tif")):
        regrid(path, dataset, template, row0, row1, virtual_points=virtual_points)