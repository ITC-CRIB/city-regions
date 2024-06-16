import numpy
import rasterio

from tqdm.auto import tqdm

# level0_path = "GADM_Level0.tif"
# level1_path = "GADM_Level1.tif"
# offset = 5000

level0_path = "GADM_Level1_Filled.tif"
level1_path = "GADM_Level2.tif"
offset = 50000

level0_dataset = rasterio.open(level0_path)
level0_grid = level0_dataset.read(1)
level0_nodata = level0_dataset.nodatavals[0]

level1_dataset = rasterio.open(level1_path)
level1_grid = level1_dataset.read(1)
level1_nodata = level1_dataset.nodatavals[0]

for row in tqdm(range(level1_grid.shape[0])):
    for col in range(level1_grid.shape[1]):

        val0 = level0_grid[row, col]
        val1 = level1_grid[row, col]
        
        if val1 != level1_nodata:
            continue
            
        if val0 != level0_nodata:
            level1_grid[row][col] = offset + val0

with rasterio.open(
    level1_path.replace(".tif", "_Filled.tif"),
    "w",
    driver="GTiff",
    height=level1_grid.shape[0],
    width=level1_grid.shape[1],
    count=1,
    dtype=numpy.int32,
    crs=level1_dataset.crs,
    transform=level1_dataset.transform,
    nodata=level1_nodata,
    compress='deflate'
) as grid:
    grid.write(level1_grid, 1)
grid.close()
    
level1_grid = None
level0_grid = None

level1_dataset.close()
level0_dataset.close()