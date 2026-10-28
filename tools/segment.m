// segment <in> <outMask.png>  -> prints JSON {"w","h","faces":[[x,y,w,h],...]} (pixels, top-left origin)
// Foreground mask is restricted to the instance under the largest detected face.
#import <Foundation/Foundation.h>
#import <Vision/Vision.h>
#import <CoreImage/CoreImage.h>
#import <ImageIO/ImageIO.h>

int main(int argc, const char **argv) {
    @autoreleasepool {
        NSURL *url = [NSURL fileURLWithPath:@(argv[1])];
        CGImageSourceRef src = CGImageSourceCreateWithURL((__bridge CFURLRef)url, NULL);
        CGImageRef cg = CGImageSourceCreateImageAtIndex(src, 0, NULL);
        size_t W = CGImageGetWidth(cg), H = CGImageGetHeight(cg);
        VNImageRequestHandler *handler = [[VNImageRequestHandler alloc] initWithCGImage:cg options:@{}];
        VNGenerateForegroundInstanceMaskRequest *fg = [VNGenerateForegroundInstanceMaskRequest new];
        VNDetectFaceRectanglesRequest *face = [VNDetectFaceRectanglesRequest new];
        NSError *err = nil;
        if (![handler performRequests:@[fg, face] error:&err]) { fprintf(stderr, "%s\n", err.description.UTF8String); return 1; }
        NSMutableArray *faces = [NSMutableArray array];
        VNFaceObservation *big = nil;
        for (VNFaceObservation *f in face.results) {
            CGRect b = f.boundingBox;
            [faces addObject:@[@((int)(b.origin.x * W)), @((int)((1 - CGRectGetMaxY(b)) * H)), @((int)(b.size.width * W)), @((int)(b.size.height * H))]];
            if (!big || b.size.width > big.boundingBox.size.width) big = f;
        }
        VNInstanceMaskObservation *obs = fg.results.firstObject;
        if (obs) {
            NSIndexSet *inst = obs.allInstances;
            if (big) {
                CVPixelBufferRef m = obs.instanceMask;
                CVPixelBufferLockBaseAddress(m, kCVPixelBufferLock_ReadOnly);
                size_t mw = CVPixelBufferGetWidth(m), mh = CVPixelBufferGetHeight(m), rb = CVPixelBufferGetBytesPerRow(m);
                uint8_t *p = CVPixelBufferGetBaseAddress(m);
                long cx = (long)(CGRectGetMidX(big.boundingBox) * mw), cy = (long)((1 - CGRectGetMidY(big.boundingBox)) * mh);
                cx = MAX(0, MIN((long)mw - 1, cx)); cy = MAX(0, MIN((long)mh - 1, cy));
                uint8_t label = p[cy * rb + cx];
                CVPixelBufferUnlockBaseAddress(m, kCVPixelBufferLock_ReadOnly);
                if (label) inst = [NSIndexSet indexSetWithIndex:label];
            }
            CVPixelBufferRef pb = [obs generateScaledMaskForImageForInstances:inst fromRequestHandler:handler error:&err];
            if (!pb) { fprintf(stderr, "%s\n", err.description.UTF8String); return 1; }
            CIImage *ci = [CIImage imageWithCVPixelBuffer:pb];
            CIContext *ctx = [CIContext context];
            CGColorSpaceRef gray = CGColorSpaceCreateDeviceGray();
            [ctx writePNGRepresentationOfImage:ci toURL:[NSURL fileURLWithPath:@(argv[2])] format:kCIFormatL8 colorSpace:gray options:@{} error:&err];
        }
        NSData *json = [NSJSONSerialization dataWithJSONObject:@{@"w": @(W), @"h": @(H), @"faces": faces} options:0 error:nil];
        printf("%s\n", [[NSString alloc] initWithData:json encoding:NSUTF8StringEncoding].UTF8String);
    }
    return 0;
}
