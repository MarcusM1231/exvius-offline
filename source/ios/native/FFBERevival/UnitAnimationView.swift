import SwiftUI
import UIKit
import CryptoKit

struct UnitAnimationMetadata: Decodable {
    let masterID: String
    let kind: String
    let ticks: [Int]
    let frames: [String]
    let width: Int
    let height: Int
    let timebase: Int
    let anchor: [Int]
}
final class UnitAnimationClip {
    let metadata: UnitAnimationMetadata
    let images: [UIImage]
    init(metadata: UnitAnimationMetadata, images: [UIImage]) { self.metadata = metadata; self.images = images }
    static let expectedLock = "83da4a54c78b70d7fa6240b56da8b86aabdc0ef4008937f06d3fea4867c58a4b"
    static func load(masterID: String, kind: String = "idle", directory: URL? = Bundle.main.resourceURL?.appendingPathComponent("UnitAnimations")) -> UnitAnimationClip? {
        guard masterID.count == 9, masterID.allSatisfy(\.isNumber), ["idle","standby"].contains(kind), let directory else { return nil }
        do {
            let receiptData = try Data(contentsOf: directory.appendingPathComponent("receipt.json"))
            let receipt = try JSONSerialization.jsonObject(with: receiptData) as? [String: Any]
            guard receipt?["lock_sha256"] as? String == expectedLock, let hashes = receipt?["files"] as? [String:String] else { return nil }
            func checked(_ name: String) throws -> Data {
                let data = try Data(contentsOf: directory.appendingPathComponent(name))
                guard data.count < 2_000_000, hashes[name] == SHA256.hash(data: data).map({ String(format: "%02x", $0) }).joined() else { throw CocoaError(.fileReadCorruptFile) }
                return data
            }
            let catalog = try JSONDecoder().decode([String:[String:UnitAnimationMetadata]].self, from: checked("catalog.json"))
            guard let m = catalog[masterID]?[kind], m.masterID == masterID, m.kind == kind,
                  (1...64).contains(m.frames.count), m.frames.count == m.ticks.count,
                  m.ticks.allSatisfy({ (1...600).contains($0) }), m.timebase == 60,
                  (1...512).contains(m.width), (1...512).contains(m.height), m.width*m.height*m.frames.count*4 <= 8_388_608,
                  m.anchor.count == 2, m.anchor.allSatisfy({ abs($0) <= 512 }) else { return nil }
            var images: [UIImage] = []
            for (index,name) in m.frames.enumerated() {
                guard name == "\(masterID)/\(kind)/\(index).png" else { return nil }
                let data = try checked(name)
                guard data.starts(with: [137,80,78,71,13,10,26,10]), let image = UIImage(data:data)?.preparingForDisplay(),
                      image.cgImage?.width == m.width, image.cgImage?.height == m.height else { return nil }
                images.append(image)
            }
            return UnitAnimationClip(metadata:m,images:images)
        } catch { return nil }
    }
    func image(at elapsed: Double) -> UIImage {
        images[UnitAnimationClock.frame(at:elapsed,ticks:metadata.ticks)]
    }
}

// Frames are assembled from the original part records at import time. The same
// origin is retained for every frame; no per-frame trimming, IO or texture cache.
struct UnitAnimationView: UIViewRepresentable {
    let clip: UnitAnimationClip
    let elapsed: Double
    let scale: Double
    func makeUIView(context: Context) -> UnitAnimationSurface { UnitAnimationSurface() }
    func updateUIView(_ view: UnitAnimationSurface, context: Context) {
        view.render(clip:clip,time:elapsed,scale:scale)
    }
}
final class UnitAnimationSurface: UIView {
    private let pixels = CALayer()
    private var current: (UnitAnimationClip, Double, Double)?
    override func layoutSubviews() {
        super.layoutSubviews()
        if let (clip,time,scale) = current { render(clip:clip,time:time,scale:scale) }
    }
    override init(frame: CGRect) {
        super.init(frame:frame);isUserInteractionEnabled = false
        pixels.magnificationFilter = .nearest; pixels.minificationFilter = .nearest
        layer.addSublayer(pixels)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    func render(clip: UnitAnimationClip,time: Double,scale: Double) {
        current = (clip,time,scale)
        let m = clip.metadata
        CATransaction.begin(); CATransaction.setDisableActions(true)
        pixels.contents = clip.image(at:time).cgImage
        pixels.frame = CGRect(x:bounds.midX-Double(m.anchor[0])*scale,y:bounds.maxY-Double(m.anchor[1])*scale,width:Double(m.width)*scale,height:Double(m.height)*scale)
        CATransaction.commit()
    }
}

@MainActor private final class UnitAnimationTick: NSObject {
    weak var owner: UnitAnimationPreviewController?
    @objc func tick(_ link: CADisplayLink) { owner?.tick(link.timestamp) }
}
@MainActor final class UnitAnimationPreviewController: ObservableObject {
    @Published var clock = UnitAnimationClock()
    @Published var clip: UnitAnimationClip?
    private var link: CADisplayLink?
    private var target: UnitAnimationTick?
    private var previous: Double?
    var requestedPlaying = true
    func load(_ id: String, _ kind: String) { clip = nil;clip = UnitAnimationClip.load(masterID:id,kind:kind);clock.restart();previous=nil }
    func play() {
        requestedPlaying=true;clock.paused=false
        guard link == nil else { return }
        previous=nil;let target=UnitAnimationTick();target.owner=self;self.target=target
        let display=CADisplayLink(target:target,selector:#selector(UnitAnimationTick.tick(_:)))
        display.preferredFrameRateRange=CAFrameRateRange(minimum:30,maximum:30,preferred:30)
        display.add(to:.main,forMode:.common);link=display
    }
    func pause(user: Bool = true) { if user { requestedPlaying=false };clock.paused=true;link?.invalidate();link=nil;target=nil;previous=nil }
    fileprivate func tick(_ time: Double) { let delta=previous.map { min(0.1,max(0,time-$0)) } ?? 0;previous=time;clock.advance(delta) }
    deinit { link?.invalidate() }
}
struct UnitAnimationPreview: View {
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @StateObject private var controller = UnitAnimationPreviewController()
    @State private var masterID: String
    init(masterID: String = "202000203") { _masterID = State(initialValue: masterID) }
    @State private var kind="idle"
    @State private var compare=false
    var body: some View {
        VStack {
            Text("Original unit parts · reconstructed playback routing").font(.caption)
            Text("\(UnitAnimationLibrary.entries.first(where: {$0.master_id == masterID})?.name ?? "Unit") · \(masterID)").font(.headline)
            NavigationLink("Choose another unit") { UnitAnimationGallery() }
            Picker("Animation",selection:$kind) {Text("Idle").tag("idle");if UnitAnimationLibrary.entries.first(where: {$0.master_id == masterID})?.supported.contains("standby") == true {Text("Standby").tag("standby")}}.pickerStyle(.segmented)
            ZStack(alignment:.bottom) {
                Color(red:0.08,green:0.09,blue:0.16)
                if let clip=controller.clip, !compare {
                    UnitAnimationView(clip:clip,elapsed:reduceMotion ? 0 : controller.clock.elapsed,scale:2.8)
                } else if let url=UnitCatalog.display(masterID:masterID,backendName:nil,rarity:nil,isAward:false).artworkURL,let image=UIImage(contentsOfFile:url.path) {
                    Image(uiImage:image).resizable().interpolation(.none).scaledToFit().frame(height:180)
                } else { Text("No exact-ID static artwork").padding() }
            }.frame(height:280).clipped()
            Toggle("Compare static artwork",isOn:$compare)
            if let clip=controller.clip {Text("\(masterID) · frame \(UnitAnimationClock.frame(at:controller.clock.elapsed,ticks:clip.metadata.ticks)+1)/\(clip.images.count) · 60-tick research timebase").font(.caption).monospacedDigit()} else {Text(UnitAnimationLibrary.entries.first(where: {$0.master_id == masterID})?.reason ?? "Animation unavailable: exact-ID static fallback").font(.caption)}
            HStack {
                Button("Play") {controller.play()};Button("Pause") {controller.pause()}
                Button("Restart") {controller.clock.restart();controller.play()}
            }.buttonStyle(.bordered)
            Slider(value:$controller.clock.speed,in:0.25...2,step:0.25)
            Text(String(format:"Speed %.2f×",controller.clock.speed)).font(.caption)
            Spacer()
        }.padding().navigationTitle("Unit animation research")
            .task {controller.load(masterID,kind);if !reduceMotion {controller.play()}}
            .onChange(of:masterID) {_ in controller.load(masterID,kind)}
            .onChange(of:kind) {_ in controller.load(masterID,kind)}
            .onChange(of:scenePhase) {phase in if phase == .active && controller.requestedPlaying {controller.play()} else if phase != .active {controller.pause(user:false)}}
            .onDisappear {controller.pause();controller.clip=nil}
    }
}
