<?php
require_once("../code/common.php");

$pops = getPopulations();

printf("Population datasets are %s.\n", implode(", ", $pops));

$area = $argv[1];
if (empty($area)) {
	echo "Please specify the area type.";
	exit(1);
}
echo "Area type is {$area}.\n";

$data = readCSV("pop_{$area}.csv", "id");

echo "Calculating coherence matrix...\n";
$matrix = [];
$n = count($pops);
foreach ($data as $id => $row) {
	$types = [];
	foreach ($pops as $key) {
		$types[] = findType($row[$key]);
	}
	for ($i = 0; $i < $n; $i++) {
		$a = $pops[$i] . "_" . $types[$i];
		$matrix[$a][$a]++;
		for ($j = $i + 1; $j < $n; $j++) {
			$b = $pops[$j] . "_" . $types[$j];
			$matrix[$a][$b]++;
			$matrix[$b][$a]++;
		}
	}
}
$keys = [];
foreach ($pops as $key) {
	for ($i = 0; $i <= 4; $i++) {
		$keys[] = $key . "_" . $i;
	}
}

echo "Writing coherence matrix...\n";
$file = fopen("coherence_{$area}.csv", "w");
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