<?php
require_once("../code/common.php");

function nextPow($val) {
	if($val < 2) return 1;
	for($i = 0 ; $val > 1 ; $i++) {
		$val = $val >> 1;
	}
	return 1 << ($i + 1);
}

$ref = $argv[1];
if (empty($ref)) {
	echo "Please specify the reference population.";
	exit(1);
}
else if (!in_array($ref, getAreas())) {
	echo "Invalid reference area {$ref}.";
	exit(1);
}
echo "Reference area is {$ref}.\n";

echo "Reading data...\n";
$rows = readCSV("type.csv", "id");
$keys = [];
$counts = [];
foreach ($rows as $row) {
	if (empty($keys)) {
		$keys = array_keys($row);
	}
	$counts[$row[$ref]]++;
}

echo "Finding breaking points...\n";
krsort($counts);
$ids = [];
$start = 0;
foreach ($counts as $key => $val) {
	$ids[$key] = $start;
	//$start += nextPow($val);
	$start = (floor(($start + $val) / 1000) + 1) * 1000;
}

printf("Breaking points are %s.\n", implode(", ", $ids));

echo "Sorting...\n";
usort($rows, function ($a, $b) use ($ref) {
	return $a[$ref] - $b[$ref] ?: $a["id"] - $b["id"];
});

echo "Relabeling...\n";
foreach ($rows as &$row) {
	$type = $row[$ref];
	$row[] = ++$ids[$type];
}
unset($row);

echo "Saving relabelled data...\n";
$file = fopen("type_relabel.csv", "w");
fprintf($file, "%s,city_id\n", implode(",", $keys));
foreach ($rows as $row) {
	fprintf($file, "%s\n", implode(",", $row));
}
fclose($file);
?>