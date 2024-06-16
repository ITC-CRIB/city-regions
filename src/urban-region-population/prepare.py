import rasterio
import numpy as np

region_datasets = {
    "City_Region_Systems_1h": 10000,
    "City_Region_Systems_2h": 10000,
    "City_Region_Systems_3h": 10000,
    "L1_City_Regions_1h": 100000,
    "L1_City_Regions_2h": 100000,
    "L1_City_Regions_3h": 100000,
    "L2_City_Regions_1h": 100000,
    "L2_City_Regions_2h": 100000,
    "L2_City_Regions_3h": 100000,    
    "L3_City_Regions_1h": 100000,
    "L3_City_Regions_2h": 100000,
    "L3_City_Regions_3h": 100000,    
    "L4_City_Regions_1h": 100000,
    "L4_City_Regions_2h": 100000,
    "L4_City_Regions_3h": 100000,    
}

print("Reading country dataset...")
country_dataset = rasterio.open("../country/grid/GADM_Level0_Full.tif")
country_data = country_dataset.read(1).astype(np.int32)

for region, offset in region_datasets.items():
    print(f"Reading {region} dataset...")
    
    region_dataset = rasterio.open(f"../urban-region/{region}.tif")
    region_data = region_dataset.read(1).astype(np.int32)

    print("  Merging datasets...")
    data = country_data * offset + region_data
    data = np.where(region_data == region_dataset.nodata, 0, data)
    #data = np.where(data < offset, 0, data)
    #data = np.where(data % offset, data, 0)

    print("  Saving merged dataset...")
    with rasterio.open(
        f"{region}_GADM_Level0.tif",
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