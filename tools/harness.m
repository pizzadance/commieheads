// harness <saver bundle> <outdir> <width> <height> <seconds> <snapEvery> : load the .saver like legacyScreenSaver does, snapshot frames
#import <Cocoa/Cocoa.h>
#import <ScreenSaver/ScreenSaver.h>
int main(int argc, const char **argv) {
    @autoreleasepool {
        [NSApplication sharedApplication];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];
        NSBundle *b = [NSBundle bundleWithPath:@(argv[1])];
        NSError *e = nil;
        if (![b loadAndReturnError:&e]) { NSLog(@"load failed %@", e); return 1; }
        Class c = b.principalClass;
        NSLog(@"principal class: %@", c);
        NSRect r = NSMakeRect(0, 0, atof(argv[3]), atof(argv[4]));
        ScreenSaverView *v = [[c alloc] initWithFrame:r isPreview:NO];
        NSWindow *w = [[NSWindow alloc] initWithContentRect:r styleMask:NSWindowStyleMaskBorderless backing:NSBackingStoreBuffered defer:NO];
        w.contentView = v;
        [v startAnimation];
        double total = atof(argv[5]), every = atof(argv[6]), t0 = CACurrentMediaTime(), next = every; int n = 0;
        while (CACurrentMediaTime() - t0 < total) {
            [v animateOneFrame];
            [[NSRunLoop currentRunLoop] runUntilDate:[NSDate dateWithTimeIntervalSinceNow:1.0 / 60]];
            if (CACurrentMediaTime() - t0 >= next) {
                NSBitmapImageRep *rep = [v bitmapImageRepForCachingDisplayInRect:v.bounds];
                [v cacheDisplayInRect:v.bounds toBitmapImageRep:rep];
                NSString *p = [NSString stringWithFormat:@"%s/shot_%02d.png", argv[2], n++];
                [[rep representationUsingType:NSBitmapImageFileTypePNG properties:@{}] writeToFile:p atomically:YES];
                next += every;
            }
        }
    }
    return 0;
}
