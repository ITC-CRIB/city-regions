<?php
require_once("../code/common.php");

$regions = [
	"City_Region_Systems" => [10000, "class"],
	"L1_City_Regions" => [100000, "id,type,origin"],
	"L2_City_Regions" => [100000, "id,type,origin"],
	"L3_City_Regions" => [100000, "id,type,origin"],
	"L4_City_Regions" => [100000, "id,type,origin"],
];

$zones = [
	"1h",
	"2h",
	"3h",
];

$populations = getPopulations();

$countries = readCSV("../country/GADM_Level0.csv", "fid");

$types = readCSV("../urban/type_country.csv", "id");

foreach ($regions as $region => list($factor, $fields)) {
	$fields = explode(",", $fields);
	echo "Processing region {$region}.\n";
	foreach ($zones as $zone) {
		echo " Processing zone {$zone}:\n";
		$data = [];
		foreach ($populations as $population) {
			echo "  Reading population data {$population}...\n";
			$rows = readCSV("{$region}_{$zone}_GADM_Level0_{$population}.csv");
			foreach ($rows as $row) {
				$val = round($row["sum"]);
				if ($val == 0.0) continue;
				$data[$row["zone"]][$population] = $val;				
			}
		}
		ksort($data);
		echo " Saving merged population data...\n";
		$file = fopen("{$region}_{$zone}_GADM_Level0.csv", "w");
		fprintf($file, "country_id,country_code,%s,%s\n", implode(",", $fields), implode(",", $populations));
		foreach ($data as $id => $vals) {
			$country = floor($id / $factor);
			$id = $id % $factor;
			$row = [
				$country,
				$countries[$country]["GID_0"],
			];
			foreach ($fields as $field) {
				switch ($field) {
					case "class":
						$row[] = $id;
						break;
					case "id":
						$row[] = $id;
						break;
					case "type":
						$row[] = $types[$id]["type"];
						break;
					case "origin":
						$row[] = $types[$id]["country_code"];
						break;
					default:
						throw new \Exception("Invalid field {$field}.");
				}
			}
			foreach ($populations as $population) {
				$row[] = $vals[$population];
			}
			fprintf($file, "%s\n", implode(",", $row));
		}
		fclose($file);
	}	
}
?>