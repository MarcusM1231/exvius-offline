"""Regenerate the checked-in Xcode project with Python's standard library."""
from pathlib import Path
import plistlib

root = Path(__file__).resolve().parent
settings = {
    'PRODUCT_NAME': '$(TARGET_NAME)', 'SWIFT_VERSION': '5.0',
    'IPHONEOS_DEPLOYMENT_TARGET': '16.0', 'TARGETED_DEVICE_FAMILY': '1,2',
    'SDKROOT': 'iphoneos', 'SUPPORTED_PLATFORMS': 'iphoneos iphonesimulator',
    'CODE_SIGN_STYLE': 'Automatic', 'INFOPLIST_FILE': 'FFBERevival/Info.plist',
    'CURRENT_PROJECT_VERSION': '1', 'MARKETING_VERSION': '0.1.0',
    'GENERATE_INFOPLIST_FILE': 'NO', 'ENABLE_USER_SCRIPT_SANDBOXING': 'NO',
    'SWIFT_OBJC_BRIDGING_HEADER': 'Bridge/FFBERevival-Bridging-Header.h',
    'LD_RUNPATH_SEARCH_PATHS': '$(inherited) @executable_path/Frameworks',
    'FRAMEWORK_SEARCH_PATHS': '$(inherited) $(PROJECT_DIR)/../.local/runtime',
    'CLANG_ENABLE_OBJC_ARC': 'YES',
    'FFBE_UNIT_CONTENT': 'preservation', 'FFBE_SUMMON_UI': 'original',
}
def uid(n): return '%024X' % n
objects = {}
def put(n, **value): objects[uid(n)] = value; return uid(n)
project = put(1, isa='PBXProject', attributes={'LastUpgradeCheck': '2620'},
    buildConfigurationList=uid(8), compatibilityVersion='Xcode 14.0',
    developmentRegion='en', knownRegions=['en', 'Base'], mainGroup=uid(2),
    productRefGroup=uid(3), projectDirPath='', projectRoot='', targets=[uid(4)])
files = sorted((root / 'FFBERevival').glob('*.swift')) + [root / 'Bridge/PythonBridge.m']
put(2, isa='PBXGroup', children=[uid(100+i) for i in range(len(files))]+[uid(18),uid(61),uid(3)], sourceTree='<group>')
put(3, isa='PBXGroup', children=[uid(5)], name='Products', sourceTree='<group>')
put(4, isa='PBXNativeTarget', buildConfigurationList=uid(9), buildPhases=[uid(6), uid(15), uid(7), uid(16), uid(17)],
    buildRules=[], dependencies=[], name='FFBERevival', productName='FFBERevival',
    productReference=uid(5), productType='com.apple.product-type.application')
put(5, isa='PBXFileReference', explicitFileType='wrapper.application', includeInIndex='0',
    path='FFBERevival.app', sourceTree='BUILT_PRODUCTS_DIR')
put(6, isa='PBXSourcesBuildPhase', buildActionMask='2147483647', files=[uid(200+i) for i in range(len(files))], runOnlyForDeploymentPostprocessing='0')
put(7, isa='PBXResourcesBuildPhase', buildActionMask='2147483647', files=[], runOnlyForDeploymentPostprocessing='0')
for i, file in enumerate(files):
    put(100+i, isa='PBXFileReference', lastKnownFileType='sourcecode.c.objc' if file.suffix == '.m' else 'sourcecode.swift', path=str(file.relative_to(root)), sourceTree='<group>')
    put(200+i, isa='PBXBuildFile', fileRef=uid(100+i))
put(61, isa='PBXFileReference', lastKnownFileType='text.xcconfig', path='Build.xcconfig', sourceTree='<group>')
put(18, isa='PBXFileReference', lastKnownFileType='wrapper.xcframework', path='../.local/runtime/Python.xcframework', sourceTree='<group>')
put(19, isa='PBXBuildFile', fileRef=uid(18))
put(60, isa='PBXBuildFile', fileRef=uid(18), settings={'ATTRIBUTES':['CodeSignOnCopy','RemoveHeadersOnCopy']})
put(15, isa='PBXFrameworksBuildPhase', buildActionMask='2147483647', files=[uid(19)], runOnlyForDeploymentPostprocessing='0')
put(16, isa='PBXShellScriptBuildPhase', buildActionMask='2147483647', files=[], inputPaths=[], outputPaths=[],
    name='Package Python runtime and backend', shellPath='/bin/sh',
    shellScript='set -eu\n/usr/bin/python3 "$PROJECT_DIR/scripts/package_python.py"\n',
    alwaysOutOfDate='1', runOnlyForDeploymentPostprocessing='0')
put(17, isa='PBXCopyFilesBuildPhase', buildActionMask='2147483647', dstPath='', dstSubfolderSpec='10',
    files=[uid(60)], name='Embed Python Framework', runOnlyForDeploymentPostprocessing='0')
for base, configlist, target in [(10,8,False),(12,9,True)]:
    for i, name in enumerate(['Debug','Release']):
        config = dict(settings) if target else {'CLANG_ENABLE_MODULES':'YES'}
        if target:
            config['SWIFT_OPTIMIZATION_LEVEL'] = '-Onone' if name == 'Debug' else '-O'
        put(base+i, isa='XCBuildConfiguration', buildSettings=config, name=name,
            **({'baseConfigurationReference':uid(61)} if target else {}))
    put(configlist, isa='XCConfigurationList', buildConfigurations=[uid(base),uid(base+1)], defaultConfigurationIsVisible='0', defaultConfigurationName='Release')
output = root / 'FFBERevival.xcodeproj/project.pbxproj'
output.parent.mkdir(exist_ok=True)
output.write_bytes(plistlib.dumps({'archiveVersion':'1','classes':{},'objectVersion':'56','objects':objects,'rootObject':project}, sort_keys=False))
print(output)
