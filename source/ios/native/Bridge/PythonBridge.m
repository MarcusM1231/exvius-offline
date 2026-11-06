#import "PythonBridge.h"
#import <Python/Python.h>

@implementation PythonBridge
static BOOL ready = NO;
static NSString *initializationFailure = nil;

+ (void)fail:(NSString *)message error:(NSError **)error {
    if (error) *error = [NSError errorWithDomain:@"FFBEPython" code:1
                                    userInfo:@{NSLocalizedDescriptionKey: message}];
}

+ (BOOL)initializeAt:(NSString *)resources error:(NSError **)error {
    if (ready) return YES;
    if (initializationFailure) { [self fail:initializationFailure error:error]; return NO; }
    PyPreConfig preconfig;
    PyPreConfig_InitIsolatedConfig(&preconfig);
    preconfig.utf8_mode = 1;
    PyStatus status = Py_PreInitialize(&preconfig);
    if (PyStatus_Exception(status)) {
        initializationFailure = @"Python pre-initialization failed";
        [self fail:initializationFailure error:error]; return NO;
    }
    PyConfig config;
    PyConfig_InitIsolatedConfig(&config);
    config.write_bytecode = 0;
    config.buffered_stdio = 0;
    config.install_signal_handlers = 0;
    config.module_search_paths_set = 1;
    NSString *home = [resources stringByAppendingPathComponent:@"python"];
    status = PyConfig_SetBytesString(&config, &config.home, home.UTF8String);
    NSArray *paths = @[
        [home stringByAppendingPathComponent:@"lib/python3.13"],
        [home stringByAppendingPathComponent:@"lib/python3.13/lib-dynload"],
        [resources stringByAppendingPathComponent:@"PythonApp/source/ios/embedded"]
    ];
    for (NSString *path in paths) {
        if (PyStatus_Exception(status)) break;
        wchar_t *wide = Py_DecodeLocale(path.UTF8String, NULL);
        if (!wide) { status = PyStatus_Error("Could not decode module path"); break; }
        status = PyWideStringList_Append(&config.module_search_paths, wide);
        PyMem_RawFree(wide);
    }
    if (!PyStatus_Exception(status)) status = Py_InitializeFromConfig(&config);
    if (PyStatus_Exception(status)) {
        initializationFailure = [NSString stringWithFormat:@"Python initialization failed: %s",
                                 status.err_msg ?: "unknown error"];
        PyConfig_Clear(&config);
        [self fail:initializationFailure error:error]; return NO;
    }
    PyConfig_Clear(&config);
    // The dispatch queue can move between OS threads. Release the initial GIL,
    // then use PyGILState_Ensure/Release around every call on that queue.
    PyEval_SaveThread();
    ready = YES;
    return YES;
}

+ (NSString *)call:(NSString *)request resources:(NSString *)resources error:(NSError **)error {
    if (![self initializeAt:resources error:error]) return nil;
    PyGILState_STATE gil = PyGILState_Ensure();
    PyObject *module = PyImport_ImportModule("offline_entry");
    PyObject *function = module ? PyObject_GetAttrString(module, "dispatch") : NULL;
    PyObject *argument = PyUnicode_FromString(request.UTF8String);
    PyObject *result = function && argument ? PyObject_CallOneArg(function, argument) : NULL;
    const char *text = result && PyUnicode_Check(result) ? PyUnicode_AsUTF8(result) : NULL;
    NSString *response = text ? [NSString stringWithUTF8String:text] : nil;
    if (!response) {
        if (PyErr_Occurred()) PyErr_Print();
        [self fail:@"Python call failed; see Xcode console for details" error:error];
    }
    Py_XDECREF(result); Py_XDECREF(argument); Py_XDECREF(function); Py_XDECREF(module);
    PyGILState_Release(gil);
    return response;
}
@end
