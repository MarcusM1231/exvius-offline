import SwiftUI
import CryptoKit

// This library is separate from the production idle catalog and pin.
enum UnitActionLibrary {
    static let expectedLock="1d133fd9957524bdfe08a05c0048ebfe8280aad0755abf3dd8d4cbdbc195452e"
    static let kinds=["idle","standby","atk","magic_atk","win_before","win"]
    static let ids=["202000203","100000103","206000103","206000113","100004604","205000703"]
    static let root=Bundle.main.resourceURL?.appendingPathComponent("UnitActionResearch")
    static func checked(_ name:String,directory:URL?=root) throws -> Data {
        guard let directory else {throw CocoaError(.fileNoSuchFile)}
        let receipt=try JSONSerialization.jsonObject(with:Data(contentsOf:directory.appendingPathComponent("receipt.json"))) as? [String:Any]
        let data=try Data(contentsOf:directory.appendingPathComponent(name))
        guard receipt?["lock_sha256"] as? String==expectedLock,let hashes=receipt?["files"] as? [String:String],data.count<2_000_000,
              hashes[name]==SHA256.hash(data:data).map({String(format:"%02x",$0)}).joined() else {throw CocoaError(.fileReadCorruptFile)}
        return data
    }
    static let catalog:[String:[String:UnitAnimationMetadata]] = {
        guard let data=try? checked("catalog.json"),let result=try? JSONDecoder().decode([String:[String:UnitAnimationMetadata]].self,from:data),Set(result.keys)==Set(ids) else {return [:]}
        return result
    }()
    static let unsupported:[String:[String:String]] = {
        guard let data=try? checked("support.json"),let result=try? JSONSerialization.jsonObject(with:data) as? [String:[String:Any]] else {return [:]}
        return result.mapValues {$0["unsupported"] as? [String:String] ?? [:]}
    }()
    static func clip(_ id:String,_ kind:String,directory:URL?=root) -> UnitAnimationClip? {
        UnitAnimationClip.load(masterID:id,kind:kind,directory:directory,expectedDigest:expectedLock,allowedKinds:kinds)
    }
    static func title(_ kind:String) -> String {
        ["idle":"Idle","standby":"Standby","atk":"Attack","magic_atk":"Magic Attack","win_before":"Victory Entrance","win":"Victory"][kind] ?? kind
    }
}

@MainActor final class UnitActionResearchController: ObservableObject {
    let driver=UnitAnimationPreviewController()
    @Published private(set) var clip:UnitAnimationClip?
    @Published private(set) var plan:UnitActionPlan?
    @Published private(set) var sample=UnitActionSample(segment:0,localTime:0,completed:false,holding:false)
    @Published private(set) var explanation="Select an original action or an experimental preset."
    @Published private(set) var completedCount=0
    private(set) var masterID="100004604"
    private var loadedSegment = -1
    private var notified=false
    var onCompletion:(() -> Void)?
    init() {driver.onAdvance={ [weak self] time in self?.update(time) }}
    func configure(id:String,actions:[String],hold:Double=0,repeats:Bool=false,autoplay:Bool=true) {
        driver.pause();clip=nil;plan=nil;loadedSegment = -1;notified=false;completedCount=0;masterID=id;driver.clock.restart();sample=UnitActionSample(segment:0,localTime:0,completed:false,holding:false)
        do {
            let available=(UnitActionLibrary.catalog[id] ?? [:]).mapValues(\.ticks)
            let newPlan=try UnitActionPlan(actions:actions,available:available,hold:hold,repeats:repeats)
            plan=newPlan;explanation="Original part frames · 60-tick research timebase · experimental routing"
            update(0)
            if autoplay && plan != nil {driver.play()}
        } catch {
            let missing=actions.first {(UnitActionLibrary.catalog[id] ?? [:])[$0]==nil} ?? actions.first ?? "action"
            explanation="Cannot play \(UnitActionLibrary.title(missing)): \(UnitActionLibrary.unsupported[id]?[missing] ?? "missing or invalid action data"). Showing exact-ID idle/static fallback."
            clip=UnitActionLibrary.clip(id,"idle") ?? UnitAnimationClip.load(masterID:id)
        }
    }
    func update(_ time:Double) {
        guard let plan else {return}
        let next=plan.sample(at:time)
        if next.segment != loadedSegment {
            clip=nil
            guard let loaded=UnitActionLibrary.clip(masterID,plan.segments[next.segment].kind) else {
                self.plan=nil;driver.pause();explanation="Action resource failed validation; safe idle/static fallback."
                clip=UnitAnimationClip.load(masterID:masterID);return
            }
            clip=loaded;loadedSegment=next.segment
        }
        sample=next
        if next.completed && !notified {
            notified=true;completedCount += 1;driver.pause();onCompletion?()
        }
    }
    func play() {
        guard plan != nil else {return}
        if sample.completed {restart()} else {driver.play()}
    }
    func pause() {driver.pause()}
    func restart() {
        guard plan != nil else {return}
        driver.pause();driver.clock.restart();notified=false;completedCount=0;loadedSegment = -1;update(0);driver.play()
    }
    func suspend() {driver.pause(user:false)}
    func resumeIfRequested() {if driver.requestedPlaying {driver.play()}}
    func stop() {driver.pause();clip=nil;plan=nil;onCompletion=nil;loadedSegment = -1}
    var currentAction:String {guard let plan else {return "fallback"};return plan.segments[sample.segment].kind}
}

struct UnitActionResearchView: View {
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @StateObject private var controller=UnitActionResearchController()
    @State private var id="100004604"
    @State private var choice="idle"
    @State private var preset=UnitActionPreset.current
    @State private var sequenceMode=false
    @State private var repeatResearch=false
    @State private var hold=0.0
    @State private var speed=1.0
    @State private var compareStatic=false
    @State private var zoom=1.0
    @State private var staticImage: UIImage?
    var body:some View {
        ScrollView {
            VStack(spacing:12) {
                Text("DEVELOPER RESEARCH · NOT ORIGINAL ROUTING").font(.caption).foregroundStyle(.purple)
                Text("No campaign, Lapis, rewards or production summon access.").font(.caption)
                selection
                stage
                playbackDetails
                settings
            }.padding()
        }.navigationTitle("Action comparison")
            .task {loadStaticImage();configure()}
            .onChange(of:id) {_ in loadStaticImage();configure()}.onChange(of:choice) {_ in configure()}
            .onChange(of:preset) {_ in configure()}.onChange(of:sequenceMode) {_ in configure()}
            .onChange(of:repeatResearch) {_ in configure()}.onChange(of:hold) {_ in configure()}
            .onChange(of:speed) {controller.driver.clock.speed=$0}
            .onChange(of:scenePhase) {phase in if phase == .active {controller.resumeIfRequested()} else {controller.suspend()}}
            .onDisappear {controller.stop();staticImage=nil}
    }
    private var selection: some View {
        VStack(spacing:12) {
                Picker("Exact unit",selection:$id) {
                    ForEach(UnitActionLibrary.ids,id:\.self) {uid in
                        Text("\(UnitActionLibrary.entriesName(uid)) · \(uid)").tag(uid)
                    }
                }
                Toggle("Experimental sequence",isOn:$sequenceMode)
                if sequenceMode {
                    Picker("Preset",selection:$preset) {ForEach(UnitActionPreset.allCases,id:\.self) {p in Text(p.label).tag(p).disabled(p.actions.contains {UnitActionLibrary.catalog[id]?[$0]==nil})}}
                    Text("Presets are hypotheses for comparison, not recovered summon instructions.").font(.caption)
                } else {
                    Picker("Action",selection:$choice) {
                        ForEach(UnitActionLibrary.kinds,id:\.self) {kind in
                            Text(UnitActionLibrary.title(kind)+(UnitActionLibrary.catalog[id]?[kind]==nil ? " · unsupported" : "")).tag(kind).disabled(UnitActionLibrary.catalog[id]?[kind]==nil)
                        }
                    }
                }

        }
    }
    private var stage: some View {
        VStack(spacing:12) {
                ZStack(alignment:.bottom) {
                    Color(red:0.06,green:0.07,blue:0.12)
                    if compareStatic,let image=staticImage {
                        Image(uiImage:image).resizable().interpolation(.none).scaledToFit().frame(height:170)
                    } else if let clip=controller.clip {
                        GeometryReader {geometry in
                            UnitAnimationView(clip:clip,elapsed:reduceMotion ? 0 : controller.sample.localTime,scale:fitScale(width:geometry.size.width)*zoom)
                                .frame(height:280)
                        }
                    } else {Text("Exact-ID static/missing-art fallback").foregroundStyle(.white).padding()}
                }.frame(height:330).clipped()

        }
    }
    private var playbackDetails: some View {
        VStack(spacing:12) {
                Text("\(id) · \(UnitActionLibrary.title(controller.currentAction)) · frame \(controller.clip.map {UnitAnimationClock.frame(at:controller.sample.localTime,ticks:$0.metadata.ticks)+1} ?? 0)")
                    .font(.caption).monospacedDigit()
                Text(controller.explanation).font(.caption)
                if let plan=controller.plan {Text(String(format:"%.3f / %.3f s · %@",min(controller.driver.clock.elapsed,plan.duration),plan.duration,controller.sample.completed ? "finished (held last frame)" : controller.sample.holding ? "explicit research hold" : "playing / paused")).font(.caption)}
                HStack {Button("Play") {controller.play()};Button("Pause") {controller.pause()};Button("Restart") {controller.restart()};Button("Stop") {controller.stop()}}.buttonStyle(.bordered)

        }
    }
    private var settings: some View {
        VStack(spacing:12) {
                Slider(value:$zoom,in:0.5...3,step:0.25)
                Text(String(format:"Research zoom %.2f× · 1× fits all action bounds; larger zoom can crop effects",zoom)).font(.caption)
                Toggle("Static comparison",isOn:$compareStatic)
                Toggle("Repeat entire research selection",isOn:$repeatResearch)
                Text("Finite actions play once by default. Repetition is an explicit research setting.").font(.caption)
                Slider(value:$speed,in:0.25...2,step:0.25)
                Text(String(format:"Speed %.2f×",speed)).font(.caption)
                if sequenceMode {
                    Slider(value:$hold,in:0...2,step:0.1)
                    Text(String(format:"Research hold between actions %.1f s (not original timing)",hold)).font(.caption)
                }
                ForEach(UnitActionLibrary.kinds.filter {UnitActionLibrary.catalog[id]?[$0]==nil},id:\.self) {kind in
                    Text("\(UnitActionLibrary.title(kind)): \(UnitActionLibrary.unsupported[id]?[kind] ?? "not imported")").font(.caption).foregroundStyle(.secondary)
                }

        }
    }
    private func fitScale(width:Double) -> Double {
        let clips=Array((UnitActionLibrary.catalog[id] ?? [:]).values)
        let reach=clips.map {max($0.anchor[0],$0.width-$0.anchor[0])}.max() ?? 1
        let up=clips.map {$0.anchor[1]}.max() ?? 1
        let down=clips.map {$0.height-$0.anchor[1]}.max() ?? 1
        return min(2,min(width*0.46/Double(max(1,reach)),min(275/Double(max(1,up)),45/Double(max(1,down)))))
    }
    private func loadStaticImage() {
        staticImage=nil
        if let url=UnitCatalog.display(masterID:id,backendName:nil,rarity:nil,isAward:false).artworkURL {staticImage=UIImage(contentsOfFile:url.path)}
    }
    private func configure() {
        controller.configure(id:id,actions:sequenceMode ? preset.actions : [choice],hold:sequenceMode ? hold : 0,repeats:repeatResearch,autoplay:!reduceMotion && scenePhase == .active)
        controller.driver.clock.speed=speed
    }
}
extension UnitActionLibrary {
    static func entriesName(_ id:String) -> String {UnitAnimationLibrary.entries.first {$0.master_id==id}?.name ?? id}
}
