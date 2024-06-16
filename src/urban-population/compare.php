<?php
require_once("../code/common.php");

$limits = getLimits();

$pop = $argv[1];
if (empty($pop)) {
	echo "Please specify the population dataset.";
	exit(1);
}
echo "Population dataset is {$pop}.\n";

$data = [];
$areas = [];
foreach (getAreas() as $area) {
	$filename = "pop_{$area}.csv";
	if (!file_exists($filename)) continue;
	$areas[] = $area;
	echo "Processing {$filename}...\n";
	$rows = readCSV($filename, "id");
	foreach ($rows as $id => $row) {
		$data[$id][$area] = $row[$pop];
	}
}
printf("Areas are %s.\n", implode(", ", $areas));
printf("Population limits are %s.\n", implode(", ", $limits));
echo "Writing output file...\n";
ksort($data);
$matrix = [];
$n = count($areas);
$file = fopen("compare_{$pop}.csv", "w");
fprintf($file, "id,%s,%s_type\n", implode(",", $areas), implode("_type,", $areas));
foreach ($data as $id => $vals) {
	$row = [$id];
	foreach ($areas as $key) {
		$row[] = round($vals[$key]);
	}
	$types = [];
	foreach ($areas as $key) {
		$type = findType($vals[$key]);
		$types[] = $type;
		$row[] = $type;
	}
	for ($i = 0; $i < $n; $i++) {
		$a = $areas[$i] . "_" . $types[$i];
		$matrix[$a][$a]++;
		for ($j = $i + 1; $j < $n; $j++) {
			$b = $areas[$j] . "_" . $types[$j];
			$matrix[$a][$b]++;
			$matrix[$b][$a]++;			
		}
	}
	fprintf($file, "%s\n", implode(",", $row));
}
fclose($file);

$keys = [];
foreach ($areas as $key) {
	for ($i = 0, $n = count($limits); $i <= $n; $i++) {
		$keys[] = $key . "_" . $i;
	}
}

echo "Writing coherence matrix...\n";
$file = fopen("coherence_{$pop}.csv", "w");
fprintf($file, "type,%s\n", implode(",", $keys));
foreach ($keys as $key) {
	$row = [$key];
	foreach ($keys as $otherKey) {
		$row[] = $matrix[$key][$otherKey];
	}
	fprintf($file, "%s\n", implode(",", $row));
}
fclose($file);
?>