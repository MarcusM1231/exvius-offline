"""Xcode build phase: bundle read-only code/data and signed iOS extension frameworks."""
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
IOS = Path(__file__).resolve().parents[2]
SOURCE = IOS.parent
RUNTIME = IOS / '.local/runtime/Python.xcframework'
MODULES = ('data_paths', 'player_state', 'ffbe_config', 'ffbe_state', 'ffbe_gacha', 'season')


def copy_tree(source, destination):
    shutil.copytree(source, destination, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'test', 'tests'))


def package_code(destination):
    """Preserve the existing service's relative source/server path contract."""
    destination = Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    prototype = destination / 'source/ios/prototype'
    embedded = destination / 'source/ios/embedded'
    server = destination / 'source/server'
    for path in (prototype, embedded, server):
        path.mkdir(parents=True)
    for name in ('summon_service.py', 'demo_data.py'):
        shutil.copy2(IOS / 'prototype' / name, prototype / name)
    shutil.copy2(IOS / 'embedded/offline_entry.py', embedded / 'offline_entry.py')
    for module in MODULES:
        shutil.copy2(SOURCE / 'server' / (module + '.py'), server)
    for name in ('gacha_authored.json', 'nv_vision_cards.json', 'seasons.json'):
        shutil.copy2(SOURCE / 'server' / name, server)
    # Generate using the full repository before copying just the runtime subset.
    # Metadata is generated at build time, never written to the bundle on-device.
    sys.path.insert(0, str(IOS / 'prototype'))
    from demo_data import prepare
    prepare(destination / 'metadata/demo')


def package_content(destination, mode='preservation'):
    destination = Path(destination)
    if mode not in ('preservation', 'demo'):
        raise ValueError('FFBE_UNIT_CONTENT must be preservation or demo')
    if destination.exists():
        shutil.rmtree(destination)
    if mode == 'demo':
        import json
        destination.mkdir(parents=True)
        (destination / 'catalog.json').write_text(json.dumps({'schema': 1, 'mode': 'demo', 'units': {}}))
        return
    sys.path.insert(0, str(IOS / 'content_tools'))
    from import_content import DEFAULT_OUTPUT, verify_bundle
    try:
        verify_bundle(DEFAULT_OUTPUT)
    except (OSError, ValueError) as error:
        raise RuntimeError('Unit content is missing or invalid. Run source/ios/.venv/bin/python -B '
                           'source/ios/content_tools/import_content.py --download; or build explicitly '
                           'with FFBE_UNIT_CONTENT=demo.') from error
    shutil.copytree(DEFAULT_OUTPUT, destination)


def main():
    app = Path(os.environ['TARGET_BUILD_DIR']) / os.environ['WRAPPER_NAME']
    if not RUNTIME.exists():
        raise SystemExit('Run source/ios/.venv/bin/python source/ios/native/scripts/prepare_runtime.py first')
    platform = os.environ['PLATFORM_NAME']
    if platform not in ('iphoneos', 'iphonesimulator'):
        raise SystemExit('Only iOS device and Simulator are supported')
    architectures = os.environ['ARCHS'].split()
    slice_name = 'ios-arm64' if platform == 'iphoneos' else 'ios-arm64_x86_64-simulator'
    home = app / 'python/lib'
    if home.parent.exists():
        shutil.rmtree(home.parent)
    copy_tree(RUNTIME / 'lib', home)
    for arch in architectures:
        arch_lib = RUNTIME / slice_name / ('lib-' + arch)
        if not arch_lib.exists():
            raise SystemExit('Unsupported Python slice: ' + str(arch_lib))
        for source in arch_lib.rglob('*'):
            if source.is_dir():
                continue
            target = home / source.relative_to(arch_lib)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and source.suffix == '.so':
                merged = target.with_suffix('.merged')
                subprocess.run(['xcrun', 'lipo', '-create', str(target), str(source), '-output', str(merged)], check=True)
                merged.replace(target)
            else:
                shutil.copy2(source, target)
    frameworks = app / 'Frameworks'
    frameworks.mkdir(exist_ok=True)
    # Postprocess iOS extension modules per CPython's AppleFrameworkLoader contract.
    for binary in sorted(home.rglob('*.so')):
        name = binary.name.split('.')[0]
        framework = frameworks / (name + '.framework')
        if framework.exists():
            shutil.rmtree(framework)
        framework.mkdir()
        executable = framework / name
        shutil.move(str(binary), executable)
        marker = binary.with_suffix('.fwork')
        marker.write_text(str(executable.relative_to(app)) + '\n')
        (framework / (name + '.origin')).write_text(str(marker.relative_to(app)) + '\n')
        info = {
            'CFBundleExecutable': name, 'CFBundleIdentifier': os.environ['PRODUCT_BUNDLE_IDENTIFIER'] + '.python.' + name.replace('_','-'),
            'CFBundlePackageType': 'FMWK', 'CFBundleShortVersionString': '1.0', 'CFBundleVersion': '1',
            'MinimumOSVersion': '13.0', 'CFBundleSupportedPlatforms': ['iPhoneSimulator' if platform == 'iphonesimulator' else 'iPhoneOS'],
        }
        (framework / 'Info.plist').write_bytes(plistlib.dumps(info))
        identity = os.environ.get('EXPANDED_CODE_SIGN_IDENTITY', '')
        if os.environ.get('CODE_SIGNING_ALLOWED') != 'NO':
            if not identity:
                if platform == 'iphoneos':
                    raise SystemExit('A signing identity is required for physical-device Python extensions')
                identity = '-'
            subprocess.run(['/usr/bin/codesign', '--force', '--sign', identity, '--timestamp=none', str(framework)], check=True)
    package_code(app / 'PythonApp')
    package_content(app / 'UnitContent', os.environ.get('FFBE_UNIT_CONTENT', 'preservation'))
    sys.path.insert(0, str(IOS / 'content_tools'))
    from import_summon_ui import verify, output
    ui = app / 'SummonUI'
    if ui.exists(): shutil.rmtree(ui)
    if os.environ.get('FFBE_SUMMON_UI', 'original') == 'fallback':
        ui.mkdir()
    else:
        try: verify()
        except (OSError, ValueError) as error:
            raise RuntimeError('Run python3 source/ios/content_tools/import_summon_ui.py first, or use FFBE_SUMMON_UI=fallback') from error
        shutil.copytree(output(), ui)
    from import_crystal_preview import verify as verify_crystal, output as crystal_output
    crystal = app / 'CrystalPreview'
    if crystal.exists(): shutil.rmtree(crystal)
    try:
        verify_crystal()
        shutil.copytree(crystal_output(), crystal)
    except (OSError, ValueError):
        # Optional Developer diagnostic. Missing resources must not break normal play.
        print('Crystal diagnostic unavailable; run import_crystal_preview.py to enable it')
    from import_crystal_reconstruction import verify as verify_reconstruction, output as reconstruction_output
    reconstructed = app / 'CrystalReconstruction'
    if reconstructed.exists(): shutil.rmtree(reconstructed)
    try:
        verify_reconstruction()
        shutil.copytree(reconstruction_output(), reconstructed)
    except (OSError, ValueError):
        print('Crystal reconstruction unavailable; run import_crystal_reconstruction.py to enable it')
    from import_reveal_research import verify as verify_reveal, output as reveal_output
    reveal = app / 'RevealResearch'
    if reveal.exists(): shutil.rmtree(reveal)
    try:
        verify_reveal()
        shutil.copytree(reveal_output(), reveal)
    except (OSError, ValueError):
        print('Optional reveal research unavailable; run import_reveal_research.py')
    from import_character_reveal import verify as verify_character, output as character_output
    character = app / 'CharacterReveal'
    if character.exists(): shutil.rmtree(character)
    try:
        verify_character()
        shutil.copytree(character_output(), character)
    except (OSError, ValueError):
        # Missing reveal art preserves the committed-award results-grid fallback.
        print('Character reveal unavailable; run import_character_reveal.py; results grid remains available')
    from import_crystal_entrance import verify as verify_entrance, output as entrance_output
    entrance = app / 'CrystalEntrance'
    if entrance.exists(): shutil.rmtree(entrance)
    try:
        verify_entrance()
        shutil.copytree(entrance_output(), entrance)
    except (OSError, ValueError):
        print('Optional entrance prompt/cloud unavailable; native prompt and existing crystal remain usable')
    from import_unit_attacks import verify as verify_animations, output as animation_output
    animations = app / 'UnitAnimations'
    if animations.exists(): shutil.rmtree(animations)
    try:
        verify_animations()
        shutil.copytree(animation_output(), animations)
    except (OSError, ValueError):
        raise RuntimeError('Production animation bundle missing or invalid; run import_unit_attacks.py. Existing app remains installed.')
    from import_unit_action_research import verify as verify_actions, output as action_output
    actions = app / 'UnitActionResearch'
    if actions.exists(): shutil.rmtree(actions)
    try:
        verify_actions()
        shutil.copytree(action_output(), actions)
    except (OSError, ValueError):
        print('Optional Developer action research unavailable; production animation bundle is independent')
    print('Packaged Python 3.13.11 for', platform, architectures, 'with', len(list(home.rglob('*.fwork'))), 'extension frameworks')


if __name__ == '__main__':
    main()
