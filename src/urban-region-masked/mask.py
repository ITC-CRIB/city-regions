import rasterio
import numpy as np

region_datasets = [
    "City_Region_Systems_1h",
    "City_Region_Systems_2h",
    "City_Region_Systems_3h",
    "L1_City_Regions_1h",
    "L1_City_Regions_2h",
    "L1_City_Regions_3h",
    "L2_City_Regions_1h",
    "L2_City_Regions_2h",
    "L2_City_Regions_3h",
    "L3_City_Regions_1h",
    "L3_City_Regions_2h",
    "L3_City_Regions_3h",
    "L4_City_Regions_1h",
    "L4_City_Regions_2h",
    "L4_City_Regions_3h",
]

print("Reading land mask...")
mask_dataset = rasterio.open("../land/Land_Mask.tif")
mask_data = mask_dataset.read(1).astype(np.int32)

for region in region_datasets:
    print(f"Reading {region} dataset...")

    region_dataset = rasterio.open(f"../urban-region/{region}.tif")
    region_data = region_dataset.read(1).astype(np.int32)

    print("  Masking dataset...")
    data = np.where(mask_data == mask_dataset.nodata, 0, region_data)

    print("  Saving masked dataset...")
    with rasterio.open(
        f"{region}_Masked.tif",
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=np.int32,
        crs=region_dataset.crs,
        transform=region_dataset.transform,
        nodata=0,
        compress='deflate'
    ) as grid:
        grid.write(data, 1)

    data = None
    region_dataset.close()