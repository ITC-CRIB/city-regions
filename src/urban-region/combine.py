import rasterio
import numpy as np

import gc
thresholds = [
    "1h",
    "2h",
    "3h"
]

levels = {
    "L1": 1,
    "L2": 2**16,
    "L3": 2**32,
    "L4": 2**48
}

for threshold in thresholds:
    print(f"Processing data for {threshold} threshold...")

    data = None
    crs = None
    transform = None

    for level, offset in levels.items():

        filename = f"{level}_City_Regions_{threshold}.tif"

        print(f"  Reading {filename}...")

        region_dataset = rasterio.open(filename)
        region_data = region_dataset.read(1).astype(np.int64)

        if data is None:
            if offset != 1:
                exit(f"Invalid first level offset {offset}")
            data = region_data.copy()
            crs = region_dataset.crs
            transform = region_dataset.transform

        else:
            data += region_data * offset

        region_data = None
        region_dataset.close()

        gc.collect()
    print("  Saving combined dataset...")
    with rasterio.open(
        f"City_Regions_{threshold}.tif",
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=np.int64,
        crs=crs,
        transform=transform,
        nodata=0,
        compress='deflate'
    ) as grid:
        grid.write(data, 1)
