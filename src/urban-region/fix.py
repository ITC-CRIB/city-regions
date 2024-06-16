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


def level(val):
    return 0 if val == 0 else (4 if val < 1000 else (3 if val < 3000 else (2 if val < 13000 else (1 if val < 32000 else -1))))


def fix(val):
    if not val:
        return val

    U1 = (val & np.int64(0x000000000000ffff))
    U2 = (val & np.int64(0x00000000ffff0000)) >> 16
    U3 = (val & np.int64(0x0000ffff00000000)) >> 32
    U4 = (val & np.int64(0x0fff000000000000)) >> 48

    L1 = level(U1)
    assert L1 >= 0

    L2 = level(U2)
    assert L2 >= 0

    L3 = level(U3)
    assert L3 >= 0

    L4 = level(U4)
    assert L4 >= 0

    n = 0
    while True:
        n = n + 1

        if L1:

            if L2 and L1 > L2:
                U1, L1 = U2, L2
                continue

            if L3 and L1 > L3:
                U1, L1 = U3, L3
                continue

            if L4 and L1 > L4:
                U1, L1 = U4, L4
                continue

        if L2:

            if L3 and L2 > L3:
                U2, L2 = U3, L3
                continue

            if L4 and L2 > L4:
                U2, L2 = U4, L4
                continue

        if L3:

            if L4 and L3 > L4:
                U3, L3 = U4, L4
                continue

        break

    if n == 1:
        return val

    fixed = U1 + U2 * 2**16 + U3 * 2**32 + U4 * 2**48

    print(f"{val} fixed as {fixed}, {L1}: {U1}, {L2}: {U2}, {L3}: {U3}, {L4}: {U4}")

    return fixed


for threshold in thresholds:
    print(f"Processing data for {threshold} threshold...")

    filename = f"City_Regions_{threshold}.tif"

    print(f"  Reading {filename}...")
    with rasterio.open(filename) as dataset:
        data = dataset.read(1).astype(np.int64)
        crs = dataset.crs
        transform = dataset.transform

    print(f"  Fixing grid {data.shape[0]} x {data.shape[1]}")
    fixall = np.vectorize(fix)
    fixed = fixall(data)

    filename = f"City_Regions_{threshold}_Fixed.tif"
    
    print(f"  Saving {filename}...")
    opts = {
        "driver": "GTiff",
        "height": fixed.shape[0],
        "width": fixed.shape[1],
        "count": 1,
        "dtype": np.int64,
        "crs": crs,
        "transform": transform,
        "nodata": 0,
        "compress": 'deflate',
    }
    with rasterio.open(filename, "w", **opts) as grid:
        grid.write(fixed, 1)
    
    data = None
    fixed = None
    dataset = None
    
    gc.collect()