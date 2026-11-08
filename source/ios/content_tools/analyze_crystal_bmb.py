"""Offline, checksum-pinned BMB structural report. Never emits playback data."""
import argparse
import json
from pathlib import Path
from crystal_formats import ibmb_info, ibmb_records, ibmb_resource_tables, ibmb_word_differences
from import_crystal_preview import read_source, sha

LOCK = Path(__file__).with_name('crystal-analysis.lock.json')
IOS = LOCK.parents[1]


def analyze():
    lock = json.loads(LOCK.read_text())
    sources = {key: read_source(row) for key, row in lock['sources'].items()}
    findings = {}
    for key, body in sources.items():
        header = ibmb_info(body)
        row = {'source': lock['sources'][key], 'header': header,
               'structure': ibmb_records(body),
               'compatible_with_observed_memorial_reader': header['raw_tag_04'] == 0x01030101}
        if row['compatible_with_observed_memorial_reader']:
            row['resource_tables'] = ibmb_resource_tables(body)
        findings[key] = row
    return {'schema': 1, 'lock_sha256': sha(LOCK.read_bytes()),
            'reader_evidence': lock['reader_evidence'], 'findings': findings,
            'normal_gold_aligned_word_differences': ibmb_word_differences(sources['crystal-n1'], sources['crystal-r1']),
            'original_animation_recovered': False,
            'unknowns': ['node-to-runtime-parameter mapping', 'model/texture bindings in primary tag 0x51',
                         'curve/keyframe layout', 'time units and interpolation', 'lifetimes',
                         'coordinate spaces and camera', 'blend/depth/cull state and shader semantics'],
            'warning': 'Preorder parent links and float readings are candidates. Dependency names do not establish node bindings. Tutorial and Memorial evidence must not be substituted for Global behavior.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=IOS/'.local/phase6c2/bmb-analysis.json')
    args = parser.parse_args()
    body = json.dumps(analyze(), sort_keys=True, indent=2)+'\n'
    if args.output.exists() and args.output.read_text() != body:
        raise ValueError('Refusing to overwrite differing analysis; choose a new output path')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(body)
    print(args.output)


if __name__ == '__main__':
    main()
