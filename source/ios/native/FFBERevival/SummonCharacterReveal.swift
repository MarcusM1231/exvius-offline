import SwiftUI
import UIKit
import CryptoKit

struct CharacterRevealResources {
    static let expectedLock = "3d4b171d488ef83c68d5b182c82ae4390c73ff03b0bdb5ce04e9361349041f25"
    static let names = ["cosmos","getglow","get","kirakira","glow","glow_4","starglow","stLight_3","stLight_4","stLight_5","star_0","star_1","star_3","star_4","star_5","star_glow"]
    static func load(directory: URL? = Bundle.main.resourceURL?.appendingPathComponent("CharacterReveal")) throws -> [String: UIImage] {
        guard let directory else { throw CocoaError(.fileNoSuchFile) }
        let receipt = try JSONSerialization.jsonObject(with: Data(contentsOf: directory.appendingPathComponent("receipt.json"))) as? [String: Any]
        guard receipt?["lock_sha256"] as? String == expectedLock,
              let hashes = receipt?["files"] as? [String: String],
              Set(hashes.keys) == Set(names.map { $0+".png" }+["catalog.json"]) else { throw CocoaError(.fileReadCorruptFile) }
        var images: [String: UIImage] = [:]
        for name in names+["catalog"] {
            let file = name + (name == "catalog" ? ".json" : ".png")
            let data = try Data(contentsOf: directory.appendingPathComponent(file))
            let hash = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
            guard hash == hashes[file] else { throw CocoaError(.fileReadCorruptFile) }
            if name != "catalog" {
                guard data.starts(with: [137,80,78,71,13,10,26,10]), let image = UIImage(data: data),
                      image.size.width > 0, image.size.height > 0 else { throw CocoaError(.fileReadCorruptFile) }
                images[name] = image
            }
        }
        return images
    }
}

// Trim only transparent canvas margins in memory so the visible feet meet the glow.
// Original static files and exact-ID lookup remain unchanged.
enum CharacterSpritePixels {
    static func anchored(_ image: UIImage) -> UIImage? {
        guard let cg = image.cgImage, cg.width > 0, cg.height > 0,
              cg.width <= 2048, cg.height <= 2048,
              let context = CGContext(data: nil,width: cg.width,height: cg.height,bitsPerComponent: 8,bytesPerRow: cg.width*4,
                                      space: CGColorSpaceCreateDeviceRGB(),bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue),
              let raw = context.data else { return nil }
        context.draw(cg,in: CGRect(x: 0,y: 0,width: cg.width,height: cg.height))
        let bytes = raw.assumingMemoryBound(to: UInt8.self)
        var left = cg.width, top = cg.height, right = -1, bottom = -1
        for y in 0..<cg.height { for x in 0..<cg.width where bytes[(y*cg.width+x)*4+3] != 0 {
            left = min(left,x);right = max(right,x);top = min(top,y);bottom = max(bottom,y)
        } }
        guard right >= left, bottom >= top,
              let cropped = context.makeImage()?.cropping(to: CGRect(x: left,y: top,width: right-left+1,height: bottom-top+1)) else { return nil }
        return UIImage(cgImage: cropped)
    }
}

@MainActor private final class CharacterRevealTick: NSObject {
    weak var owner: CharacterRevealController?
    @objc func step(_ link: CADisplayLink) { owner?.tick(link.timestamp) }
}
@MainActor final class CharacterRevealController: ObservableObject {
    @Published private(set) var state: CharacterRevealState
    @Published private(set) var images: [String: UIImage] = [:]
    @Published private(set) var sprite: UIImage?
    private(set) var display: UnitDisplay?
    @Published private(set) var animation: UnitAnimationClip?
    let unitMotion = ObtainedUnitMotion()
    private(set) var animationStart = 0.0
    private(set) var hasStarted = false
    private(set) var callbackCount = 0
    var onCompletion: ((CharacterRevealFinish, [Award]) -> Void)?
    private var link: CADisplayLink?
    private var target: CharacterRevealTick?
    private var previousTime: CFTimeInterval?
    var isTicking: Bool { link != nil }
    init(receipt: CommittedSummon) { state = CharacterRevealState(receipt: receipt) }
    func begin(active: Bool, directory: URL? = Bundle.main.resourceURL?.appendingPathComponent("CharacterReveal")) {
        guard !hasStarted else { return }
        hasStarted = true
        guard !state.receipt.awards.isEmpty,
              Set(state.receipt.awards.map(\.instance_id)).count == state.receipt.awards.count else { finish(.unavailable); return }
        do { images = try CharacterRevealResources.load(directory: directory) }
        catch { finish(.unavailable); return }
        guard loadCurrent() else { finish(.unavailable); return }
        if active { resume() } else { suspend() }
    }
    private func loadCurrent() -> Bool {
        guard let award = state.current else { return false }
        let unit = UnitCatalog.display(masterID: award.unit_id, backendName: award.name, rarity: award.granted_rarity, isAward: true)
        // Release the previous clip before decoding the next exact-ID animation.
        animation = nil; sprite = nil; unitMotion.clear()
        guard unit.masterID == award.unit_id else { return false }
        unitMotion.load(masterID:award.unit_id)
        animation = unitMotion.idle
        if let url = unit.artworkURL, let original = UIImage(contentsOfFile: url.path) {
            sprite = CharacterSpritePixels.anchored(original)
        }
        guard sprite != nil || animation != nil else { return false }
        animationStart = state.motionTime + CharacterRevealTiming.preparing + CharacterRevealTiming.flash
        // No reward, identity or saved receipt is changed by presentation.
        display = unit; return true
    }
    func tap(expectedInstanceID: String) {
        switch state.tap(expectedInstanceID: expectedInstanceID) {
        case .ignored: return
        case .advanced:
            previousTime = nil
            if !loadCurrent() { finish(.unavailable) }
        case .completed: notifyCompletion()
        }
    }
    func finish(_ reason: CharacterRevealFinish) {
        guard state.finish(reason) else { return }
        notifyCompletion()
    }
    private func notifyCompletion() {
        guard let reason = state.reason, callbackCount == 0 else { return }
        callbackCount += 1; invalidate()
        let callback = onCompletion; onCompletion = nil
        // Free decoded resources before crossing back to the results presenter.
        animation = nil; sprite = nil; unitMotion.clear(); display = nil; images = [:]
        callback?(reason,state.receipt.awards)
    }
    func suspend() { state.suspend(); invalidate() }
    func resume() {
        guard hasStarted, state.reason == nil, !images.isEmpty else { return }
        state.resume(); previousTime = nil
        guard link == nil else { return }
        let target = CharacterRevealTick(); target.owner = self; self.target = target
        let link = CADisplayLink(target: target,selector: #selector(CharacterRevealTick.step(_:)))
        link.preferredFrameRateRange = CAFrameRateRange(minimum: 30,maximum: 30,preferred: 30)
        link.add(to: .main,forMode: .common); self.link = link
    }
    fileprivate func tick(_ time: CFTimeInterval) {
        guard time.isFinite else { finish(.failed); return }
        let delta = previousTime.map { min(CharacterRevealTiming.maximumFrameDelta,max(0,time-$0)) } ?? 0
        previousTime = time; state.advance(delta)
    }
    private func invalidate() { link?.invalidate(); link = nil; target = nil; previousTime = nil }
    deinit { link?.invalidate() }
}

struct SummonCharacterReveal: View {
    @StateObject private var controller: CharacterRevealController
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    let completion: (CharacterRevealFinish, [Award]) -> Void
    init(receipt: CommittedSummon, controller: CharacterRevealController? = nil,
         completion: @escaping (CharacterRevealFinish, [Award]) -> Void) {
        _controller = StateObject(wrappedValue: controller ?? CharacterRevealController(receipt: receipt))
        self.completion = completion
    }
    private var state: CharacterRevealState { controller.state }
    private var material: Double {
        switch state.phase { case .preparing,.flash: return 0; case .materializing: return state.progress; default: return 1 }
    }
    private var lettering: Double {
        switch state.phase { case .preparing,.flash,.materializing: return 0; case .obtained: return state.progress; default: return 1 }
    }
    private func art(_ name: String) -> Image? { controller.images[name].map { Image(uiImage: $0) } }
    var body: some View {
        GeometryReader { geometry in
            let width = min(geometry.size.width,640)
            let sceneHeight = max(190,min(geometry.size.height*0.48,420))
            ZStack {
                Color(red: 0.018,green: 0.008,blue: 0.045).ignoresSafeArea()
                if let cosmos = art("cosmos") { cosmos.resizable().scaledToFill().opacity(0.8).frame(width: geometry.size.width,height: geometry.size.height).clipped().ignoresSafeArea() }
                VStack(spacing: 10) {
                    HStack {
                        Text("\(state.index+1) / \(state.receipt.awards.count)").font(.caption).monospacedDigit().accessibilityIdentifier("character-reveal-index")
                        Spacer()
                        Button(state.receipt.awards.count > 1 ? "Skip All" : "Skip") { controller.finish(.skipped) }
                            .accessibilityIdentifier("skip-character-reveals").disabled(state.suspended)
                    }.padding(.horizontal,20).padding(.top,12)
                    Spacer(minLength: 0)
                    stage(width: width,height: sceneHeight)
                    if let obtained = art("get") {
                        obtained.resizable().scaledToFit().frame(width: min(width*0.78,360),height: 65)
                            .opacity(lettering).accessibilityLabel("Obtained").accessibilityIdentifier("obtained-artwork")
                    }
                    VStack(spacing: 12) {
                        rarity
                        Text(state.phase == .waitingForContinue ? "Tap to Continue" : " ")
                            .font(.callout).foregroundStyle(.white.opacity(0.7))
                            .accessibilityIdentifier("tap-to-continue-prompt")
                    }.opacity(lettering).padding(.horizontal,20)
                    Spacer(minLength: 12)
                }.frame(width: width).frame(maxWidth: .infinity)
                if state.phase == .flash {
                    Color.white.opacity(0.72*(1-state.progress)).ignoresSafeArea().allowsHitTesting(false)
                }
            }.foregroundStyle(.white).contentShape(Rectangle())
                .onTapGesture { if let id = state.current?.instance_id { controller.tap(expectedInstanceID: id) } }
                .accessibilityAction(named: "Continue") { if let id = state.current?.instance_id { controller.tap(expectedInstanceID: id) } }
                .accessibilityIdentifier("character-reveal-screen")
        }.preferredColorScheme(.dark).interactiveDismissDisabled()
            .task {
                controller.onCompletion = completion
                controller.begin(active: scenePhase == .active)
            }
            .onChange(of: scenePhase) { phase in
                if phase == .active { controller.resume() } else { controller.suspend() }
            }
            .onDisappear { controller.finish(.interrupted) }
    }
    private func stage(width: Double,height: Double) -> some View {
        let baseline = height*0.83
        return ZStack {
            if let flareID = CharacterRarityArtwork.flare(state.current?.granted_rarity), let flare = art(flareID) {
                flare.resizable().scaledToFit().frame(width: 250,height: 250).blendMode(.plusLighter)
                    .opacity(material*(state.phase == .waitingForContinue ? 0.09 : 0.32)).position(x: width/2,y: baseline-90)
            }
            if let glow = art("getglow") {
                glow.resizable().scaledToFit().frame(width: min(width*0.8,300),height: 100)
                    .blendMode(.plusLighter).opacity(material*(0.88+0.08*sin(state.motionTime*1.3)))
                    .position(x: width/2,y: baseline+3)
            }
            if let playback = controller.unitMotion.sample(at:max(0,state.motionTime-controller.animationStart),reducedMotion:reduceMotion) {
                let framing = controller.unitMotion.framing(width:width,height:height,baseline:baseline)
                UnitAnimationView(clip:playback.clip,elapsed:playback.time,scale:framing.scale,horizontalAnchor:framing.anchor)
                    .frame(width:width,height:baseline)
                    .scaleEffect(reduceMotion ? 1 : 0.90+0.10*material,anchor:.bottom)
                    .opacity(material).position(x:width/2,y:baseline/2+(reduceMotion ? 0 : 12*(1-material)))
                    .accessibilityLabel("\(controller.display?.name ?? "Character") · animated unit \(state.current?.unit_id ?? "")")
                    .accessibilityIdentifier("reveal-unit-\(state.current?.unit_id ?? "missing")")
            } else if let sprite = controller.sprite {
                let scale: Double = min(3.2,min(width*0.65/Double(sprite.size.width),height*0.72/Double(sprite.size.height)))
                let spriteWidth = Double(sprite.size.width)*scale
                let spriteHeight = Double(sprite.size.height)*scale
                Image(uiImage: sprite).resizable().interpolation(.none)
                    .frame(width: spriteWidth,height: spriteHeight)
                    .scaleEffect(reduceMotion ? 1 : 0.90+0.10*material,anchor: .bottom)
                    .opacity(material).position(x: width/2,y: baseline-spriteHeight/2.0+(reduceMotion ? 0.0 : 12.0*(1-material)))
                    .accessibilityLabel("\(controller.display?.name ?? "Character") · unit \(state.current?.unit_id ?? "")")
                    .accessibilityIdentifier("reveal-unit-\(state.current?.unit_id ?? "missing")")
            }
            if let sparkle = art("kirakira") {
                ForEach(0..<5,id: \.self) { index in
                    sparkle.resizable().frame(width: 12+Double(index%3)*5,height: 12+Double(index%3)*5)
                        .blendMode(.plusLighter).opacity(material*(0.14+0.16*(1+sin(state.motionTime*1.8+Double(index)*1.9))/2))
                        .position(x: width*(0.23+Double(index)*0.135),y: baseline-35-Double((index*43)%140))
                }
            }
        }.frame(width: width,height: height).clipped()
    }
    private var rarity: some View {
        VStack(spacing: 6) {
            if let name = CharacterRarityArtwork.star(state.current?.granted_rarity),
               let count = CharacterRarityArtwork.count(state.current?.granted_rarity), let star = art(name) {
                GeometryReader { geometry in
                    let size = min(CGFloat(52),max(CGFloat(1),(geometry.size.width-CGFloat(count-1)*5)/CGFloat(count)))
                    HStack(spacing: 5) {
                        ForEach(0..<count,id: \.self) { _ in star.resizable().scaledToFit().frame(width: size,height: size) }
                    }.frame(maxWidth: .infinity)
                }.frame(height: 56)
                    .accessibilityElement(children: .ignore)
                    .accessibilityLabel("\(count) stars").accessibilityIdentifier("revealed-rarity-stars")
            } else {
                // Unsupported legacy/NV codes keep an honest fallback, never invented stars.
                Text(UnitCatalog.rarityLabel(state.current?.granted_rarity)).font(.caption).foregroundStyle(.yellow)
                    .accessibilityIdentifier("revealed-awarded-rarity")
            }
        }
    }
}

// One cover owns crystal -> character sequence -> existing grid. No second modal
// handoff and no transaction access. The parent still guards the immutable receipt ID.
struct CommittedSummonPresentation: View {
    let receipt: CommittedSummon
    let complete: ([Award]) -> Void
    var crystalController: CrystalReconstructionController? = nil
    var characterController: CharacterRevealController? = nil
    @State private var characters = false
    @State private var finished = false
    var body: some View {
        ZStack {
            if characters {
                SummonCharacterReveal(receipt: receipt,controller: characterController) { _,_ in finish() }.id(receipt.id)
            } else {
                SummonCrystalPresentation(receipt: receipt,appearance: receipt.crystalAppearance,
                                         controller: crystalController,fallback: { _ in finish() }) { _ in
                    guard !finished else { return }; characters = true
                }
            }
        }.onDisappear { finish() }.interactiveDismissDisabled()
    }
    private func finish() {
        guard !finished else { return }
        // Return directly to the saved grid rather than sliding an iOS modal sheet away.
        var transaction = Transaction(animation: nil)
        transaction.disablesAnimations = true
        withTransaction(transaction) { finished = true; complete(receipt.awards) }
    }
}
