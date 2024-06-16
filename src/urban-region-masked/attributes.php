<?php
require_once("../code/common.php");

$thresholds = ["1h", "2h", "3h"];
$levels = [
	"L1" => 1,
	"L2" => 2**16,
	"L3" => 2**32,
	"L4" => 2**48,
];

function getLevel($id) {
	$class = $id == 0 ? 0 : ($id < 1000 ? 4 : ($id < 3000 ? 3 : ($id < 13000 ? 2 : ($id < 32000 ? 1 : -1))));
	if ($class < 0) throw new \Exception("Invalid city id {$id}.");
	return $class;
}

foreach ($thresholds as $threshold) {
	echo "Processing {$threshold} threshold...\n";
	$rows = readCSV("City_Regions_{$threshold}_Masked_Fixed_Dissolved.csv");
	$file = fopen("City_Regions_{$threshold}.csv", "w");
	fputcsv($file, ["id", "code", "L1_city_id", "L2_city_id", "L3_city_id", "L4_city_id", "type"]);
	foreach ($rows as $row) {
		$val = intval($row["id"]);
		$L1 = $val % 2**16;
		$val = ($val - $L1) / 2**16;
		$L2 = $val % 2**16;
		$val = ($val - $L2) / 2**16;
		$L3 = $val % 2**16;
		$val = ($val - $L3) / 2**16;
		$L4 = $val;
		$code = sprintf("%04X-%04X-%04X-%04X", $L1, $L2, $L3, $L4);
		try {
			$type = getLevel($L1) * 1000 + getLevel($L2) * 100 + getLevel($L3) * 10 + getLevel($L4);
		}
		catch (\Exception $Exception) {
			echo "Invalid data row: {$row['id']} {$val} {$L1} {$L2} {$L3} {$L4}\n";
			exit(1);
		}
		fputcsv($file, [$row["id"], $code, $L1, $L2, $L3, $L4, $type]);
	}
	fclose($file);
}
?>