// CommieHeads — floating heads with speech bubbles.
// One head at a time drifts across a #992222 background and bounces off the edges.
// Each head is on screen for 2 s per word of its quote, then a different (random) head appears.

#import <ScreenSaver/ScreenSaver.h>
#import <QuartzCore/QuartzCore.h>

static const NSTimeInterval kFadeIn = 0.5;      // head fades in
static const NSTimeInterval kBubblePop = 0.35;  // bubble pop animation (starts after head fade-in)
static const NSTimeInterval kFadeOut = 0.6;     // head + bubble fade out at the end
static const NSTimeInterval kFlip = 0.3;        // bubble side switch (fade out, move, fade in)

@interface CommieHeadsView : ScreenSaverView
@end

@implementation CommieHeadsView {
    NSArray<NSDictionary *> *_figures;
    NSMutableDictionary<NSString *, NSImage *> *_imageCache;
    NSMutableDictionary<NSString *, NSNumber *> *_lastQuote;
    NSColor *_bg;
    double _secondsPerWord;

    NSInteger _figIndex;
    NSImage *_head;
    NSString *_quote, *_name, *_source;
    NSTimeInterval _start, _hold, _lastFrame;
    NSPoint _pos, _vel;              // head origin (bottom-left) and velocity, in points
    BOOL _bubbleRight;
    NSTimeInterval _flipStart;       // < 0 when no flip is running
    BOOL _flipTarget;
    CGFloat _bubbleWidth;            // last drawn bubble width, used to pick a side it fits on
}

- (instancetype)initWithFrame:(NSRect)frame isPreview:(BOOL)isPreview {
    if ((self = [super initWithFrame:frame isPreview:isPreview])) {
        [self setAnimationTimeInterval:1.0 / 60.0];
        NSBundle *bundle = [NSBundle bundleForClass:[self class]];
        NSData *data = [NSData dataWithContentsOfURL:[bundle URLForResource:@"quotes" withExtension:@"json"]];
        NSDictionary *cfg = data ? [NSJSONSerialization JSONObjectWithData:data options:0 error:nil] : nil;
        _figures = cfg[@"figures"] ?: @[];
        _secondsPerWord = [cfg[@"secondsPerWord"] doubleValue] ?: 2.0;
        // sRGB so the hex value is reproduced exactly
        _bg = [NSColor colorWithSRGBRed:0x99 / 255.0 green:0x22 / 255.0 blue:0x22 / 255.0 alpha:1.0];
        _imageCache = [NSMutableDictionary dictionary];
        _lastQuote = [NSMutableDictionary dictionary];
        _figIndex = -1;
        _flipStart = -1;
        if (!isPreview) {
            // macOS 14+ keeps legacyScreenSaver alive after the saver stops; quit cleanly instead of piling up instances.
            [[NSDistributedNotificationCenter defaultCenter] addObserverForName:@"com.apple.screensaver.willstop"
                                                                         object:nil queue:nil
                                                                     usingBlock:^(NSNotification *n) { exit(0); }];
        }
    }
    return self;
}

#pragma mark - Layout metrics (all relative to the view height so preview and full screen look alike)

- (CGFloat)unit { return NSHeight(self.bounds); }
- (CGFloat)headScale { return self.unit * 0.2 / 210.0; }     // heads are normalized so the face is 210 px tall
- (CGFloat)fontSize { return MAX(9.0, self.unit * 0.03); }

#pragma mark - Choosing the next head

// Words = whitespace-separated tokens containing a letter or digit (a lone dash is not a word).
static NSUInteger WordCount(NSString *s) {
    NSUInteger n = 0;
    for (NSString *w in [s componentsSeparatedByCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet])
        if ([w rangeOfCharacterFromSet:NSCharacterSet.alphanumericCharacterSet].location != NSNotFound) n++;
    return n;
}

- (NSImage *)imageNamed:(NSString *)name {
    NSImage *img = _imageCache[name];
    if (!img) {
        NSURL *u = [[NSBundle bundleForClass:[self class]] URLForResource:name withExtension:@"png" subdirectory:@"heads"];
        img = u ? [[NSImage alloc] initWithContentsOfURL:u] : nil;
        if (img) _imageCache[name] = img;
    }
    return img;
}

- (void)nextHead:(NSTimeInterval)now {
    if (_figures.count == 0) return;
    NSInteger idx;
    do { idx = SSRandomIntBetween(0, (int)_figures.count - 1); } while (_figures.count > 1 && idx == _figIndex);
    _figIndex = idx;
    NSDictionary *fig = _figures[idx];
    NSString *fid = fig[@"id"];
    _head = [self imageNamed:[NSString stringWithFormat:@"%@_%d", fid, SSRandomIntBetween(1, 3)]];

    NSArray *quotes = fig[@"quotes"];
    NSInteger q, last = _lastQuote[fid] ? _lastQuote[fid].integerValue : -1;
    do { q = SSRandomIntBetween(0, (int)quotes.count - 1); } while (quotes.count > 1 && q == last);
    _lastQuote[fid] = @(q);
    _quote = quotes[q][@"text"];
    _source = quotes[q][@"source"];
    _name = fig[@"name"];
    // The whole appearance (fades included) lasts exactly secondsPerWord x words.
    _hold = MAX(1.0, _secondsPerWord * WordCount(_quote) - (kFadeIn + kBubblePop + kFadeOut));

    NSSize hs = [self headSize];
    NSRect b = self.bounds;
    _pos = NSMakePoint(SSRandomFloatBetween(0, MAX(0, NSWidth(b) - hs.width)),
                       SSRandomFloatBetween(0, MAX(0, NSHeight(b) - hs.height)));
    double angle = SSRandomFloatBetween(0.35, 1.2) + M_PI_2 * SSRandomIntBetween(0, 3);  // avoid near-axis paths
    CGFloat speed = self.unit * 0.07;
    _vel = NSMakePoint(cos(angle) * speed, sin(angle) * speed);
    _bubbleRight = (_pos.x + hs.width / 2) < NSWidth(b) / 2;
    _flipStart = -1;
    _bubbleWidth = 0;
    _start = now;
}

- (NSSize)headSize {
    if (!_head) return NSZeroSize;
    CGFloat s = self.headScale;
    NSImageRep *rep = _head.representations.firstObject;
    CGFloat w = rep ? rep.pixelsWide : _head.size.width, h = rep ? rep.pixelsHigh : _head.size.height;
    return NSMakeSize(w * s, h * s);
}

#pragma mark - Animation

- (void)startAnimation {
    [super startAnimation];
    _lastFrame = CACurrentMediaTime();
    if (!_head) [self nextHead:_lastFrame];
}

- (void)animateOneFrame {
    NSTimeInterval now = CACurrentMediaTime();
    double dt = MIN(0.1, now - _lastFrame);
    _lastFrame = now;
    if (!_head || now - _start > kFadeIn + kBubblePop + _hold + kFadeOut) [self nextHead:now];

    NSSize hs = [self headSize];
    NSRect b = self.bounds;
    _pos.x += _vel.x * dt; _pos.y += _vel.y * dt;
    if (_pos.x < 0) { _pos.x = 0; _vel.x = fabs(_vel.x); }
    if (_pos.y < 0) { _pos.y = 0; _vel.y = fabs(_vel.y); }
    if (_pos.x + hs.width > NSWidth(b)) { _pos.x = NSWidth(b) - hs.width; _vel.x = -fabs(_vel.x); }
    if (_pos.y + hs.height > NSHeight(b)) { _pos.y = NSHeight(b) - hs.height; _vel.y = -fabs(_vel.y); }

    // Keep the bubble on the roomier side; hysteresis avoids flapping around the centre line.
    CGFloat cx = _pos.x + hs.width / 2, band = NSWidth(b) * 0.08;
    BOOL want = _bubbleRight;
    if (cx < NSWidth(b) / 2 - band) want = YES;
    else if (cx > NSWidth(b) / 2 + band) want = NO;
    // never keep the bubble on a side where it no longer fits beside the head
    CGFloat gap = self.fontSize * 1.6, margin = self.fontSize;
    BOOL fitsRight = _pos.x + hs.width + gap + _bubbleWidth <= NSWidth(b) - margin;
    BOOL fitsLeft = _pos.x - gap - _bubbleWidth >= margin;
    if (want && !fitsRight && fitsLeft) want = NO;
    else if (!want && !fitsLeft && fitsRight) want = YES;
    if (_flipStart < 0 && want != _bubbleRight) { _flipStart = now; _flipTarget = want; }
    if (_flipStart >= 0 && now - _flipStart >= kFlip / 2) _bubbleRight = _flipTarget;
    if (_flipStart >= 0 && now - _flipStart >= kFlip) _flipStart = -1;

    [self setNeedsDisplay:YES];
}

#pragma mark - Drawing

static CGFloat EaseOutBack(CGFloat t) {
    const CGFloat c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2);
}

- (void)drawRect:(NSRect)rect {
    [_bg setFill];
    NSRectFill(self.bounds);
    if (!_head) return;

    NSTimeInterval t = _lastFrame - _start, end = kFadeIn + kBubblePop + _hold;
    CGFloat fadeOut = t > end ? MAX(0, 1 - (t - end) / kFadeOut) : 1;
    CGFloat headAlpha = MIN(1, t / kFadeIn) * fadeOut;

    NSSize hs = [self headSize];
    NSRect headRect = NSMakeRect(_pos.x, _pos.y, hs.width, hs.height);
    [_head drawInRect:headRect fromRect:NSZeroRect operation:NSCompositingOperationSourceOver fraction:headAlpha
       respectFlipped:YES hints:@{NSImageHintInterpolation: @(NSImageInterpolationHigh)}];

    CGFloat pop = (t - kFadeIn) / kBubblePop;
    if (pop <= 0) return;
    CGFloat scale = pop >= 1 ? 1 : 0.6 + 0.4 * EaseOutBack(pop);
    CGFloat bubbleAlpha = MIN(1, pop) * fadeOut;
    if (_flipStart >= 0) bubbleAlpha *= fabs(1 - 2 * MIN(1, (_lastFrame - _flipStart) / kFlip));
    [self drawBubbleForHead:headRect alpha:bubbleAlpha scale:scale];
}

- (void)drawBubbleForHead:(NSRect)head alpha:(CGFloat)alpha scale:(CGFloat)scale {
    NSRect b = self.bounds;
    CGFloat fs = self.fontSize, pad = fs * 0.9, gap = fs * 1.6, margin = fs;
    CGFloat maxText = MIN(NSWidth(b) * 0.34, fs * 22);

    NSMutableParagraphStyle *ps = [NSMutableParagraphStyle new];
    ps.lineSpacing = fs * 0.15;
    NSFont *qFont = [NSFont fontWithName:@"Georgia" size:fs] ?: [NSFont systemFontOfSize:fs];
    NSFont *nFont = [NSFont fontWithName:@"AvenirNext-DemiBold" size:fs * 0.72] ?: [NSFont boldSystemFontOfSize:fs * 0.72];
    NSFont *sFont = [NSFont fontWithName:@"AvenirNext-Italic" size:fs * 0.58] ?: [NSFont systemFontOfSize:fs * 0.58];
    NSColor *ink = [NSColor colorWithSRGBRed:0.13 green:0.06 blue:0.06 alpha:1];
    NSColor *muted = [NSColor colorWithSRGBRed:0.45 green:0.30 blue:0.30 alpha:1];

    NSAttributedString *q = [[NSAttributedString alloc] initWithString:[NSString stringWithFormat:@"“%@”", _quote]
        attributes:@{NSFontAttributeName: qFont, NSForegroundColorAttributeName: ink, NSParagraphStyleAttributeName: ps}];
    NSMutableAttributedString *attr = [[NSMutableAttributedString alloc] initWithString:[@"— " stringByAppendingString:_name]
        attributes:@{NSFontAttributeName: nFont, NSForegroundColorAttributeName: ink}];
    [attr appendAttributedString:[[NSAttributedString alloc] initWithString:[@"\n" stringByAppendingString:_source]
        attributes:@{NSFontAttributeName: sFont, NSForegroundColorAttributeName: muted}]];

    NSStringDrawingOptions opt = NSStringDrawingUsesLineFragmentOrigin | NSStringDrawingUsesFontLeading;
    NSRect qr = [q boundingRectWithSize:NSMakeSize(maxText, CGFLOAT_MAX) options:opt];
    NSRect ar = [attr boundingRectWithSize:NSMakeSize(maxText, CGFLOAT_MAX) options:opt];
    CGFloat tw = ceil(MAX(NSWidth(qr), NSWidth(ar))), spacing = fs * 0.6;
    CGFloat bw = tw + 2 * pad, bh = ceil(NSHeight(qr)) + spacing + ceil(NSHeight(ar)) + 2 * pad;

    _bubbleWidth = bw;
    CGFloat bx = _bubbleRight ? NSMaxX(head) + gap : NSMinX(head) - gap - bw;
    bx = MAX(margin, MIN(NSWidth(b) - margin - bw, bx));
    CGFloat by = NSMaxY(head) - bh * 0.75;                 // bubble sits beside the upper part of the head
    by = MAX(margin, MIN(NSHeight(b) - margin - bh, by));
    NSRect br = NSMakeRect(bx, by, bw, bh);

    // Tail: from the bubble edge facing the head toward the mouth area.
    CGFloat radius = fs * 0.8;
    NSPoint mouth = NSMakePoint(_bubbleRight ? NSMaxX(head) - NSWidth(head) * 0.28 : NSMinX(head) + NSWidth(head) * 0.28,
                                NSMinY(head) + NSHeight(head) * 0.42);
    CGFloat edgeX = _bubbleRight ? NSMinX(br) : NSMaxX(br);
    CGFloat baseY = MAX(NSMinY(br) + radius + fs * 0.6, MIN(NSMaxY(br) - radius - fs * 0.6, mouth.y + fs));
    CGFloat dx = mouth.x - edgeX, dy = mouth.y - baseY, len = hypot(dx, dy), reach = MIN(len * 0.7, fs * 2.6);
    NSPoint tip = len > 0 ? NSMakePoint(edgeX + dx / len * reach, baseY + dy / len * reach) : NSMakePoint(edgeX, baseY);
    CGFloat inset = _bubbleRight ? radius : -radius;

    NSBezierPath *bubble = [NSBezierPath bezierPathWithRoundedRect:br xRadius:radius yRadius:radius];
    NSBezierPath *tail = [NSBezierPath bezierPath];
    [tail moveToPoint:NSMakePoint(edgeX + inset, baseY + fs * 0.55)];
    [tail lineToPoint:tip];
    [tail lineToPoint:NSMakePoint(edgeX + inset, baseY - fs * 0.55)];
    [tail closePath];

    CGContextRef ctx = NSGraphicsContext.currentContext.CGContext;
    CGContextSaveGState(ctx);
    CGContextSetAlpha(ctx, alpha);
    CGContextTranslateCTM(ctx, edgeX, baseY);              // pop scales out from the tail
    CGContextScaleCTM(ctx, scale, scale);
    CGContextTranslateCTM(ctx, -edgeX, -baseY);
    CGContextSetShadowWithColor(ctx, CGSizeMake(0, -fs * 0.15), fs * 0.6,
                                [NSColor colorWithSRGBRed:0.2 green:0 blue:0 alpha:0.45].CGColor);
    CGContextBeginTransparencyLayer(ctx, NULL);            // one shadow for bubble + tail
    [[NSColor colorWithSRGBRed:1 green:0.985 blue:0.96 alpha:1] setFill];
    [bubble fill];
    [tail fill];
    CGContextEndTransparencyLayer(ctx);
    CGContextSetShadowWithColor(ctx, CGSizeZero, 0, NULL);

    [q drawWithRect:NSMakeRect(bx + pad, NSMaxY(br) - pad - ceil(NSHeight(qr)), tw, ceil(NSHeight(qr))) options:opt];
    [attr drawWithRect:NSMakeRect(bx + pad, by + pad, tw, ceil(NSHeight(ar))) options:opt];
    CGContextRestoreGState(ctx);
}

- (BOOL)hasConfigureSheet { return NO; }
- (NSWindow *)configureSheet { return nil; }

@end
