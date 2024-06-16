<?php
require_once("../../code/common.php");

$levels = [0, 1, 2];
$pops = getPopulations();

foreach ($levels as $level) {
	echo "Processing level {$level}:\n";
	$data = [];
	foreach ($pops as $pop) {
		echo "Reading population data {$pop}...\n";
		$file = fopen("GADM_Level{$level}_{$pop}.csv", "r");
		$cols = [];
		while ($row = fgetcsv($file)) {
			if (empty($cols)) {
				$cols = $row;
				continue;
			}
			$row = array_combine($cols, $row);
			$val = round($row["sum"]);
			if ($val == 0.0) continue;
			$data[$row["zone"]][$pop] = $val;
		}
		fclose($file);
	}
	ksort($data);
	echo "Saving merged population data...\n";
	$file = fopen("GADM_Level{$level}.csv", "w");
	fprintf($file, "id,%s\n", implode(",", $pops));
	foreach ($data as $id => $vals) {
		$row = [$id];
		foreach ($pops as $pop) {
			$row[] = $vals[$pop];
		}
		fprintf($file, "%s\n", implode(",", $row));
	}
	fclose($file);
}


?>