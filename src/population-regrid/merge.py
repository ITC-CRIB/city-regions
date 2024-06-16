import os
import numpy as np
import rasterio

from tqdm.auto import tqdm

out = None
mask = None
nodata = -1

start = 0
end = 18000
delta = 100

for id in tqdm(range(start, end, delta)):
    source = rasterio.open(f"grid-{id}-{id+delta}.tif")

    data = source.read(1)

    if out is None:
        out = np.full((source.height, source.width), 0, dtype=np.float32)
        mask = np.full((source.height, source.width), 0, dtype=np.int16)
        crs = source.crs
        transform = source.transform

    out = np.add(out, np.where(data == source.nodata, 0, data))
    mask = np.add(mask, np.where(data == source.nodata, 0, 1))

    data = None
    source.close()

out = np.where(mask == 0, nodata, out)
    
with rasterio.open(
    f"merged-{start}-{end}.tif",
    "w",
    driver="GTiff",
    height=out.shape[0],
    width=out.shape[1],
    count=1,
    dtype=np.float32,
    crs=crs,
    transform=transform,
    nodata=nodata,
    compress="deflate"
) as grid:
    grid.write(out, 1)
grid.close()