#import <Foundation/Foundation.h>
NS_ASSUME_NONNULL_BEGIN
// Invoke only on the shared serial Python worker. Interpreter lives for the process.
@interface PythonBridge : NSObject
+ (nullable NSString *)call:(NSString *)request resources:(NSString *)resources
                     error:(NSError * _Nullable * _Nullable)error;
@end
NS_ASSUME_NONNULL_END
