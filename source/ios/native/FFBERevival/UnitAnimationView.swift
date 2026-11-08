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
    static let expectedLock = "5cc47c2422b24230f04eea0512a25254d16a4cf7ee83d7779ee649c370f6a6c2"
    static func load(masterID: String, kind: String = "idle", directory: URL? = Bundle.main.resourceURL?.appendingPathComponent("UnitAnimations"), expectedDigest: String? = nil, allowedKinds: [String] = ["idle","standby","atk"]) -> UnitAnimationClip? {
        guard masterID.count == 9, masterID.allSatisfy(\.isNumber), allowedKinds.contains(kind), let directory else { return nil }
        do {
            let receiptData = try Data(contentsOf: directory.appendingPathComponent("receipt.json"))
            let receipt = try JSONSerialization.jsonObject(with: receiptData) as? [String: Any]
            guard receipt?["lock_sha256"] as? String == (expectedDigest ?? expectedLock), let hashes = receipt?["files"] as? [String:String] else { return nil }
            func checked(_ name: String) throws -> Data {
                let data = try Data(contentsOf: directory.appendingPathComponent(name))
                guard data.count < 2_000_000, hashes[name] == SHA256.hash(data: data).map({ String(format: "%02x", $0) }).joined() else { throw CocoaError(.fileReadCorruptFile) }
                return data
            }
            let catalog = try JSONDecoder().decode([String:[String:UnitAnimationMetadata]].self, from: checked("catalog.json"))
            guard let m = catalog[masterID]?[kind], m.masterID == masterID, m.kind == kind,
                  (1...64).contains(m.frames.count), m.frames.count == m.ticks.count,
                  m.ticks.allSatisfy({ (1...600).contains($0) }), m.timebase == 60,
                  (1...(kind == "atk" ? 2048 : 512)).contains(m.width), (1...(kind == "atk" ? 1024 : 512)).contains(m.height), m.width*m.height*m.frames.count*4 <= (kind == "atk" ? 33_554_432 : 8_388_608),
                  m.anchor.count == 2, m.anchor.allSatisfy({ (-(kind == "atk" ? 4096 : 512)...(kind == "atk" ? 4096 : 512)).contains($0) }) else { return nil }
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
    var horizontalAnchor: Double = 0.5
    func makeUIView(context: Context) -> UnitAnimationSurface { UnitAnimationSurface() }
    func updateUIView(_ view: UnitAnimationSurface, context: Context) {
        view.render(clip:clip,time:elapsed,scale:scale,horizontalAnchor:horizontalAnchor)
    }
}
final class UnitAnimationSurface: UIView {
    private let pixels = CALayer()
    private var current: (UnitAnimationClip, Double, Double, Double)?
    override func layoutSubviews() {
        super.layoutSubviews()
        if let (clip,time,scale,anchor) = current { render(clip:clip,time:time,scale:scale,horizontalAnchor:anchor) }
    }
    override init(frame: CGRect) {
        super.init(frame:frame);isUserInteractionEnabled = false
        pixels.magnificationFilter = .nearest; pixels.minificationFilter = .nearest
        layer.addSublayer(pixels)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    func render(clip: UnitAnimationClip,time: Double,scale: Double,horizontalAnchor: Double = 0.5) {
        current = (clip,time,scale,horizontalAnchor)
        let m = clip.metadata
        CATransaction.begin(); CATransaction.setDisableActions(true)
        pixels.contents = clip.image(at:time).cgImage
        pixels.frame = CGRect(x:bounds.width*horizontalAnchor-Double(m.anchor[0])*scale,y:bounds.maxY-Double(m.anchor[1])*scale,width:Double(m.width)*scale,height:Double(m.height)*scale)
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
    var onAdvance: ((Double) -> Void)?
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
    fileprivate func tick(_ time: Double) { let delta=previous.map { min(0.1,max(0,time-$0)) } ?? 0;previous=time;clock.advance(delta);onAdvance?(clock.elapsed) }
    deinit { link?.invalidate() }
}
@MainActor struct UnitAnimationPreview: View {
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @StateObject private var controller = UnitAnimationPreviewController()
    @State private var motion = ObtainedUnitMotion()
    @State private var masterID: String
    @State private var kind="idle"
    @State private var compare=false
    @State private var fitEffects=false
    @State private var staticImage: UIImage?
    init(masterID: String = "202000203") { _masterID = State(initialValue: masterID) }
    private var entry: UnitAnimationEntry? {UnitAnimationLibrary.entries.first {$0.master_id==masterID}}
    private var sample: (clip:UnitAnimationClip,time:Double)? {
        if kind=="obtained" {return motion.sample(at:controller.clock.elapsed,reducedMotion:reduceMotion)}
        guard let clip=controller.clip else {return nil}
        let end=max(0,Double(clip.metadata.ticks.reduce(0,+))/60-1e-9)
        return (clip,reduceMotion ? 0 : kind=="atk" && motion.attack != nil ? min(controller.clock.elapsed,end) : controller.clock.elapsed)
    }
    var body: some View {
        ScrollView {
            VStack(spacing:12) {
                Text("Original frames · provisional OBTAINED routing").font(.caption)
                Text("\(entry?.name ?? "Unit") · \(masterID)").font(.headline)
                Picker("Playback",selection:$kind) {
                    Text("Idle").tag("idle")
                    Text("Attack").tag("atk")
                    Text("OBTAINED").tag("obtained")
                    if entry?.supported.contains("standby")==true {Text("Standby").tag("standby")}
                }.pickerStyle(.segmented)
                GeometryReader {g in
                    let f=motion.framing(width:g.size.width,height:300,baseline:250,fitEffects:fitEffects)
                    ZStack(alignment:.bottom) {
                        Color(red:0.08,green:0.09,blue:0.16)
                        if !compare,let value=sample {
                            UnitAnimationView(clip:value.clip,elapsed:value.time,scale:f.scale,horizontalAnchor:f.anchor).frame(height:250).position(x:g.size.width/2,y:125)
                        } else if let image=staticImage {
                            Image(uiImage:image).resizable().interpolation(.none).scaledToFit().frame(height:180)
                        } else {Text("No exact-ID artwork")}
                    }.frame(height:300).clipped()
                }.frame(height:300)
                Toggle("Compare static artwork",isOn:$compare)
                Toggle("Fit full effects (research)",isOn:$fitEffects)
                Text(fitEffects ? "Full-effect inspection can make the body small or off-center." : "Centered unit anchor and idle-based size. Wide effects may extend outside the viewport.").font(.caption)
                if kind=="obtained",entry?.supported.contains("idle") != true {
                    Text("OBTAINED keeps static fallback because exact-ID idle is unavailable: \(entry?.reason ?? "missing idle")").font(.caption)
                }
                if kind != "idle",entry?.supported.contains("atk") != true {
                    Text("Attack unavailable: \(entry?.unsupported?["atk"] ?? entry?.reason ?? "missing exact-ID attack"). Idle/static fallback.").font(.caption)
                }
                if let value=sample {
                    Text("\(value.clip.metadata.kind) · frame \(UnitAnimationClock.frame(at:value.time,ticks:value.clip.metadata.ticks)+1)/\(value.clip.images.count) · 60-tick research timebase").font(.caption).monospacedDigit()
                }
                HStack {
                    Button("Play") {controller.play()};Button("Pause") {controller.pause()}
                    Button("Restart") {controller.clock.restart();controller.play()}
                }.buttonStyle(.bordered)
                Slider(value:$controller.clock.speed,in:0.25...2,step:0.25)
                Text(String(format:"Speed %.2f×",controller.clock.speed)).font(.caption)
                NavigationLink("Six-unit research presets A–E") {UnitActionResearchView()}
            }.padding()
        }.navigationTitle("Original unit actions")
            .task {load();if !reduceMotion {controller.play()}}
            .onChange(of:kind) {_ in selectAction()}
            .onChange(of:scenePhase) {phase in if phase == .active && controller.requestedPlaying {controller.play()} else if phase != .active {controller.pause(user:false)}}
            .onDisappear {controller.pause();controller.clip=nil;motion.clear();staticImage=nil}
    }
    private func load() {
        motion.load(masterID:masterID,includeAttackWithoutIdle:true)
        if let url=UnitCatalog.display(masterID:masterID,backendName:nil,rarity:nil,isAward:false).artworkURL {staticImage=UIImage(contentsOfFile:url.path)}
        selectAction()
    }
    private func selectAction() {
        controller.clip=nil
        if kind=="atk" {controller.clip=motion.attack ?? motion.idle}
        else if kind=="standby" {controller.clip=UnitAnimationClip.load(masterID:masterID,kind:kind) ?? motion.idle}
        else {controller.clip=motion.idle}
        controller.clock.restart()
    }
}
