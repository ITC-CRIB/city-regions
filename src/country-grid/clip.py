import numpy
import rasterio

from tqdm.auto import tqdm

input_path = "GADM_Level2_Full.tif"
mask_path = "GADM_Level0_Simplified_0_05_Buffer_0_1_Mask.tif"

input_dataset = rasterio.open(input_path)
input_grid = input_dataset.read(1)
input_nodata = input_dataset.nodatavals[0]

mask_dataset = rasterio.open(mask_path)
mask_grid = mask_dataset.read(1)
mask_nodata = mask_dataset.nodatavals[0]

for row in tqdm(range(input_grid.shape[0])):
    for col in range(input_grid.shape[1]):

        val = input_grid[row, col]
        
        if val == input_nodata:
            continue
            
        if mask_grid[row, col] == mask_nodata:
            input_grid[row][col] = input_nodata

with rasterio.open(
    input_path.replace(".tif", "_Full_Clipped.tif"),
    "w",
    driver="GTiff",
    height=input_grid.shape[0],
    width=input_grid.shape[1],
    count=1,
    dtype=numpy.int32,
    crs=input_dataset.crs,
    transform=input_dataset.transform,
    nodata=input_nodata,
    compress='deflate'
) as grid:
    grid.write(input_grid, 1)
grid.close()
    
mask_grid = None
input_grid = None

mask_dataset.close()
input_dataset.close()