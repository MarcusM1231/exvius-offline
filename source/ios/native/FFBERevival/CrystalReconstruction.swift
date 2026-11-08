import SwiftUI
import SceneKit
import CryptoKit

private struct RecoveredCrystalMesh: Decodable {
    let schema: Int
    let vertices: Int
    let triangles: Int
    let positions: [Float]
    let normals: [Float]
    let uvs: [Float]
    let indices: [UInt32]
    let vertex_colors_raw: [UInt32]
    func geometry(indices selected: [UInt32]? = nil) throws -> SCNGeometry {
        let faceIndices = selected ?? indices
        guard schema == 1, vertices > 0, vertices <= 100000, triangles > 0, triangles <= 100000,
              positions.count == vertices*3, normals.count == vertices*3, uvs.count == vertices*2,
              vertex_colors_raw.count == vertices, indices.count == triangles*3,
              faceIndices.count % 3 == 0, faceIndices.allSatisfy({ $0 < UInt32(vertices) }),
              positions.allSatisfy(\.isFinite), normals.allSatisfy(\.isFinite), uvs.allSatisfy(\.isFinite) else {
            throw ReconstructionError.invalid("Invalid original mesh")
        }
        let p = stride(from: 0,to: positions.count,by: 3).map { SCNVector3(positions[$0],positions[$0+1],positions[$0+2]) }
        let n = stride(from: 0,to: normals.count,by: 3).map { SCNVector3(normals[$0],normals[$0+1],normals[$0+2]) }
        let uv = stride(from: 0,to: uvs.count,by: 2).map { CGPoint(x: CGFloat(uvs[$0]),y: CGFloat(uvs[$0+1])) }
        // Preserve the raw source packed-color interpretation used by the diagnostic.
        // Its shader meaning is unverified; normalized RGBA is a reconstruction choice.
        let c: [Float] = vertex_colors_raw.flatMap { word in (0..<4).map { Float((word >> ($0*8)) & 255)/255 } }
        let source = SCNGeometrySource(data: c.withUnsafeBufferPointer { Data(buffer: $0) },semantic: .color,
            vectorCount: vertices,usesFloatComponents: true,componentsPerVector: 4,bytesPerComponent: 4,dataOffset: 0,dataStride: 16)
        let element = SCNGeometryElement(data: faceIndices.withUnsafeBufferPointer { Data(buffer: $0) },primitiveType: .triangles,
            primitiveCount: faceIndices.count/3,bytesPerIndex: 4)
        return SCNGeometry(sources: [SCNGeometrySource(vertices: p),SCNGeometrySource(normals: n),SCNGeometrySource(textureCoordinates: uv),source],elements: [element])
    }
}
private enum ReconstructionError: LocalizedError {
    case invalid(String)
    var errorDescription: String? { if case .invalid(let message) = self { return message }; return nil }
}
private struct ReconstructionReceipt: Decodable { let files: [String: String] }

// Weak display-link target breaks the owner/link/target retain cycle.
@MainActor private final class CrystalTick: NSObject {
    weak var owner: CrystalReconstructionController?
    @objc func step(_ link: CADisplayLink) { owner?.tick(link.timestamp) }
}

@MainActor final class CrystalReconstructionController: ObservableObject {
    @Published private(set) var ready = false
    @Published private(set) var message = "Loading original assets…"
    private(set) var clock = CrystalClock()
    @Published var appearance: CrystalAppearance = .blue { didSet { recolor(); render() } }
    @Published var baseVisible = true { didSet { render() } }
    @Published var glossVisible = true { didSet { render() } }
    @Published var highlightsVisible = true { didSet { render() } }
    @Published var glowVisible = true { didSet { render() } }
    @Published var particlesVisible = true { didSet { render() } }
    @Published var partialVisible = false { didSet { render() } }
    @Published var alternateModels = false { didSet { if ready { rebuildModels() } } }
    var onCompletion: ((CrystalPlaybackOutcome) -> Void)?
    let view = SCNView(frame: .zero)
    private(set) var callbackCount = 0
    private(set) var frameIntervals: [Double] = []
    private(set) var loadCount = 0
    private var meshes: [String: RecoveredCrystalMesh] = [:]
    private var images: [String: UIImage] = [:]
    private var scene: SCNScene?
    private let crystal = SCNNode()
    private let fragments = SCNNode()
    private var base = SCNNode(), gloss = SCNNode(), highlights = SCNNode(), partial = SCNNode()
    private var halo = SCNNode(), beam = SCNNode(), burst = SCNNode()
    private var stars: [SCNNode] = []
    private var pieces: [SCNNode] = []
    private let fallingRoot = SCNNode()
    private var fallers: [SCNNode] = []
    private var cloud = SCNNode()
    private var entranceImages: [String: UIImage] = [:]
    var touchPromptImage: UIImage? { entranceImages["touchscreen"] }
    var entranceAssetsAvailable: Bool { !entranceImages.isEmpty }
    var visibleFallingCount: Int { fallers.filter { !$0.isHidden && $0.opacity > 0 }.count }
    var entranceElapsed: Double? { tapClock?.phase == .fallingCrystals ? tapClock?.elapsed : nil }
    private var link: CADisplayLink?
    private var target: CrystalTick?
    private var previousTime: CFTimeInterval?
    private var pendingCompletion = false
    private var tapClock: TapSummonClock?
    var tapPhase: TapSummonPhase? { tapClock?.phase }
    var showsTouchPrompt: Bool { tapClock?.showsTouchPrompt ?? false }
    var productionSourceTime: Double? { tapClock?.sourceTime }
    var productionMotionTime: Double? { tapClock?.motionTime }
    func startTapPresentation(includeFalling: Bool = true) {
        guard ready else { onCompletion?(.unavailable); return }
        cancel(); tapClock = TapSummonClock(includeFalling: includeFalling); pendingCompletion = true
        clock.restart(); startLink(); render(); objectWillChange.send()
    }
    func inspectTouchState() {
        guard ready else { return }
        cancel(); tapClock = TapSummonClock(); tapClock?.advance(CrystalEntranceTiming.totalArrival)
        tapClock?.suspend(); pendingCompletion = true; clock.restart(); clock.pause(); render(); objectWillChange.send()
    }
    @discardableResult func tapToBreak() -> Bool {
        guard tapClock?.tap() == true else { return false }
        render(); objectWillChange.send(); return true
    }
    func resumeTapPresentation() {
        guard tapClock != nil, pendingCompletion else { return }
        tapClock?.resume(); clock.play(); previousTime = nil; startLink(); render(); objectWillChange.send()
    }
    private(set) var resourceBytes = 0
    var nodeCount: Int { var count = 0; scene?.rootNode.enumerateChildNodes { _,_ in count += 1 }; return count }
    var isTicking: Bool { link != nil }
    var layerVisibility: [String: Bool] { ["base": !base.isHidden,"gloss": !gloss.isHidden,"highlights": !highlights.isHidden,"partial": !partial.isHidden,"glow": !halo.isHidden,"particles": stars.contains { !$0.isHidden }] }
    var stage: String { tapPhase?.rawValue ?? CrystalPose.sample(clock.time).stage }
    var speed: Double { get { clock.speed } set { clock.speed = newValue } }
    private var tint: UIColor { color(for: appearance) }
    private func color(for appearance: CrystalAppearance) -> UIColor {
        switch appearance {
        case .blue: return UIColor(red: 0.12,green: 0.64,blue: 1,alpha: 1)
        case .gold: return UIColor(red: 1,green: 0.62,blue: 0.09,alpha: 1)
        case .rainbow: return UIColor(red: 0.56,green: 0.87,blue: 1,alpha: 1)
        }
    }
    static var resourceDirectory: URL? {
        Bundle.main.resourceURL?.appendingPathComponent(ProcessInfo.processInfo.arguments.contains("--crystal-assets-missing") ? "AbsentReconstruction" : "CrystalReconstruction")
    }
    func load(directory: URL? = nil, entranceDirectory: URL? = CrystalEntranceResources.directory) {
        cancel(); ready = false; loadCount += 1
        do {
            guard let root = directory ?? Self.resourceDirectory else { throw ReconstructionError.invalid("Missing resource folder") }
            let receipt = try JSONDecoder().decode(ReconstructionReceipt.self,from: Data(contentsOf: root.appendingPathComponent("receipt.json")))
            let expected = Set((1...5).map { String(format: "model%03d.json",$0) } + ["texture001.png","texture002.png","texture004.png","prismatic.png","glow.png","halo.png","burst.png","catalog.json"])
            guard Set(receipt.files.keys) == expected else { throw ReconstructionError.invalid("Unexpected resource manifest") }
            var data: [String: Data] = [:]
            for (name,digest) in receipt.files {
                let bytes = try Data(contentsOf: root.appendingPathComponent(name))
                guard bytes.count < 4*1024*1024, SHA256.hash(data: bytes).map({ String(format: "%02x",$0) }).joined() == digest else {
                    throw ReconstructionError.invalid("Resource checksum failed: " + name)
                }
                data[name] = bytes
            }
            var decoded: [String: RecoveredCrystalMesh] = [:]
            for i in 1...5 {
                let key = String(format: "model%03d",i)
                guard let bytes = data[key+".json"] else { throw ReconstructionError.invalid("Missing mesh") }
                let mesh = try JSONDecoder().decode(RecoveredCrystalMesh.self,from: bytes)
                _ = try mesh.geometry(); decoded[key] = mesh
            }
            var textures: [String: UIImage] = [:]
            for key in ["texture001","texture002","texture004","prismatic","glow","halo","burst"] {
                guard let bytes = data[key+".png"], let image = UIImage(data: bytes) else { throw ReconstructionError.invalid("Invalid texture") }
                textures[key] = image
            }
            entranceImages = (try? CrystalEntranceResources.load(entranceDirectory)) ?? [:]
            meshes = decoded; images = textures; resourceBytes = data.values.reduce(0) { $0+$1.count }
            buildScene(); ready = true; inspect()
            message = "Original assets · reconstructed layers, materials and motion"
        } catch {
            clearScene(); meshes.removeAll(); images.removeAll(); entranceImages.removeAll(); message = "Preview unavailable: " + error.localizedDescription
        }
    }
    private func clearScene() {
        invalidateLink(); view.scene = nil; scene = nil
        crystal.removeFromParentNode(); fragments.removeFromParentNode()
        crystal.childNodes.forEach { $0.removeFromParentNode() }; fragments.childNodes.forEach { $0.removeFromParentNode() }
        stars.removeAll(); pieces.removeAll()
        fallingRoot.removeFromParentNode(); fallingRoot.childNodes.forEach { $0.removeFromParentNode() }
        fallers.removeAll(); cloud.removeFromParentNode(); cloud = SCNNode()
    }
    private func buildScene() {
        clearScene()
        let scene = SCNScene(); self.scene = scene
        scene.rootNode.addChildNode(crystal); crystal.addChildNode(fragments)
        scene.rootNode.addChildNode(fallingRoot)
        if let image = entranceImages["cloud"] {
            cloud = SCNNode(geometry: SCNPlane(width: 100,height: 130))
            let m = SCNMaterial(); m.lightingModel = .constant; m.diffuse.contents = image
            m.multiply.contents = UIColor(white: 0.65,alpha: 1); m.diffuse.wrapS = .repeat; m.diffuse.wrapT = .repeat
            m.writesToDepthBuffer = false; m.readsFromDepthBuffer = false
            cloud.geometry?.materials = [m]; cloud.position.z = -22; cloud.renderingOrder = -10
            scene.rootNode.addChildNode(cloud)
        }
        let camera = SCNNode(); camera.camera = SCNCamera(); camera.position = SCNVector3(0,1,48)
        camera.camera?.usesOrthographicProjection = true; camera.camera?.orthographicScale = 18
        camera.camera?.zNear = 0.1; camera.camera?.zFar = 200
        camera.camera?.wantsHDR = true; camera.camera?.bloomIntensity = 0.65
        camera.camera?.bloomThreshold = 0.85; camera.camera?.bloomBlurRadius = 8
        scene.rootNode.addChildNode(camera); view.pointOfView = camera
        let ambient = SCNNode(); ambient.light = SCNLight(); ambient.light?.type = .ambient; ambient.light?.intensity = 300
        scene.rootNode.addChildNode(ambient)
        let light = SCNNode(); light.light = SCNLight(); light.light?.type = .omni; light.light?.intensity = 650
        light.position = SCNVector3(-12,18,25); scene.rootNode.addChildNode(light)
        halo = billboard("glow",width: 29,height: 38,z: -5,order: -3)
        beam = billboard("glow",width: 9,height: 65,z: -6,order: -4)
        burst = billboard("burst",width: 43,height: 43,z: 8,order: 10)
        for node in [halo,beam,burst] { scene.rootNode.addChildNode(node) }
        for i in 0..<28 {
            let node = billboard(i%4 == 0 ? "burst" : "glow",width: i%4 == 0 ? 1.1 : 0.35,height: i%4 == 0 ? 1.1 : 0.35,z: 9,order: 9)
            stars.append(node); scene.rootNode.addChildNode(node)
        }
        view.scene = scene; view.backgroundColor = UIColor(red: 0.008,green: 0.018,blue: 0.045,alpha: 1)
        view.antialiasingMode = .multisampling4X; view.preferredFramesPerSecond = 60
        view.allowsCameraControl = false; view.autoenablesDefaultLighting = false
        rebuildModels()
    }
    private func billboard(_ texture: String,width: CGFloat,height: CGFloat,z: Float,order: Int) -> SCNNode {
        let node = SCNNode(geometry: SCNPlane(width: width,height: height))
        let material = SCNMaterial(); material.lightingModel = .constant; material.diffuse.contents = images[texture]
        material.blendMode = .add; material.writesToDepthBuffer = false; material.readsFromDepthBuffer = false
        material.isDoubleSided = true; node.geometry?.materials = [material]; node.position.z = z; node.renderingOrder = order
        return node
    }
    private func material(_ texture: String,additive: Bool) -> SCNMaterial {
        let m = SCNMaterial(); m.diffuse.contents = images[texture]; m.isDoubleSided = true
        m.lightingModel = additive ? .constant : .blinn
        m.blendMode = additive ? .add : .alpha
        m.writesToDepthBuffer = !additive; m.readsFromDepthBuffer = !additive
        m.specular.contents = UIColor(white: 0.9,alpha: 1); m.shininess = 70
        m.diffuse.wrapS = .repeat; m.diffuse.wrapT = .repeat
        return m
    }
    private func rebuildModels() {
        do {
            for n in [base,gloss,highlights,partial] { n.removeFromParentNode() }
            fragments.childNodes.forEach { $0.removeFromParentNode() }; pieces.removeAll()
            guard let shell = meshes[alternateModels ? "model004" : "model001"],
                  let second = meshes[alternateModels ? "model005" : "model002"], let partialMesh = meshes["model003"] else {
                throw ReconstructionError.invalid("Missing layer model")
            }
            base = SCNNode(geometry: try shell.geometry()); base.geometry?.materials = [material("texture001",additive: false)]
            gloss = SCNNode(geometry: try second.geometry()); gloss.geometry?.materials = [material(alternateModels ? "texture002" : "halo",additive: true)]
            highlights = SCNNode(geometry: try shell.geometry()); highlights.geometry?.materials = [material("texture004",additive: true)]
            partial = SCNNode(geometry: try partialMesh.geometry()); partial.geometry?.materials = [material("halo",additive: true)]
            gloss.scale = SCNVector3(1.001,1.001,1.001); highlights.scale = SCNVector3(1.002,1.002,1.002)
            gloss.renderingOrder = 2; highlights.renderingOrder = 3; partial.renderingOrder = 4
            for node in [base,gloss,highlights,partial] { crystal.addChildNode(node) }
            // Reconstructed 12 clusters of the original surface triangles. No invented
            // shard vertices and no claim that model003 is an original fracture mesh.
            var groups = [[UInt32]](repeating: [],count: 12)
            for i in stride(from: 0,to: shell.indices.count,by: 3) {
                let ids = Array(shell.indices[i..<i+3]); let x = ids.reduce(Float(0)) { $0+shell.positions[Int($1)*3] }/3
                let y = ids.reduce(Float(0)) { $0+shell.positions[Int($1)*3+1] }/3
                let z = ids.reduce(Float(0)) { $0+shell.positions[Int($1)*3+2] }/3
                let sector = min(5,max(0,Int((atan2(z,x)+Float.pi)/(2*Float.pi)*6)))
                groups[sector+(y>1 ? 6 : 0)].append(contentsOf: ids)
            }
            for group in groups where !group.isEmpty {
                let node = SCNNode(geometry: try shell.geometry(indices: group)); node.geometry?.materials = [material("texture001",additive: false)]
                fragments.addChildNode(node); pieces.append(node)
            }
            fallingRoot.childNodes.forEach { $0.removeFromParentNode() }; fallers.removeAll()
            for _ in 0..<(CrystalEntranceTiming.count-1) {
                let node = SCNNode()
                for (index,source) in [base,gloss,highlights].enumerated() {
                    let layer = source.clone(); layer.name = "entrance-layer-"+String(index)
                    layer.geometry = source.geometry?.copy() as? SCNGeometry
                    layer.geometry?.materials = source.geometry?.materials.compactMap { $0.copy() as? SCNMaterial } ?? []
                    layer.isHidden = false; node.addChildNode(layer)
                }
                let trail = billboard("glow",width: 6,height: 55,z: -1,order: -1)
                trail.name = "original-glow-trail"; trail.position.y = 22; trail.opacity = 0.26
                node.addChildNode(trail); fallingRoot.addChildNode(node); fallers.append(node)
            }
            recolor(); render()
        } catch { ready = false; cancel(); message = "Layer build failed: " + error.localizedDescription }
    }
    private func applySurface(_ material: SCNMaterial?,appearance: CrystalAppearance) {
        let tint = color(for: appearance)
        material?.diffuse.contents = images[appearance == .rainbow ? "prismatic" : "texture001"]
        material?.multiply.contents = appearance == .rainbow ? UIColor.white : tint
        material?.lightingModel = appearance == .rainbow ? .constant : .blinn
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        tint.getRed(&r,green: &g,blue: &b,alpha: &a)
        material?.emission.contents = UIColor(red: r*0.045,green: g*0.045,blue: b*0.045,alpha: 1)
    }
    private func recolor() {
        applySurface(base.geometry?.firstMaterial,appearance: appearance)
        gloss.geometry?.firstMaterial?.multiply.contents = tint
        highlights.geometry?.firstMaterial?.multiply.contents = UIColor(white: 0.75,alpha: 1)
        partial.geometry?.firstMaterial?.multiply.contents = tint
        for node in [halo,beam,burst]+stars { node.geometry?.firstMaterial?.multiply.contents = tint }
        for node in pieces { node.geometry?.firstMaterial?.multiply.contents = tint }
        for (index,node) in fallers.enumerated() {
            // Background colors are decorative, as in the reference; only the hero
            // uses the immutable receipt's cosmetic rarity. These are not rewards.
            let style = FallingCrystalPose.decorativeAppearance(index: index)
            node.childNode(withName: "entrance-layer-0",recursively: false)?.opacity = 0.95
            node.childNode(withName: "entrance-layer-1",recursively: false)?.opacity = style == .rainbow ? 0.10 : 0.24
            node.childNode(withName: "entrance-layer-2",recursively: false)?.opacity = style == .rainbow ? 0.07 : 0.19
            applySurface(node.childNode(withName: "entrance-layer-0",recursively: false)?.geometry?.firstMaterial,appearance: style)
            node.childNode(withName: "entrance-layer-1",recursively: false)?.geometry?.firstMaterial?.multiply.contents = color(for: style)
            node.childNode(withName: "original-glow-trail",recursively: false)?.geometry?.firstMaterial?.multiply.contents = color(for: style)
        }
    }
    func inspect() { cancel(); clock.inspect(); render(); message = "Static appearance · reconstructed layer roles" }
    func play() {
        guard ready else { onCompletion?(.unavailable); return }
        if let tapClock {
            if pendingCompletion { resumeTapPresentation() } else { startTapPresentation(includeFalling: tapClock.includesFalling) }
            return
        }
        if clock.state != .paused { cancel(); frameIntervals.removeAll(keepingCapacity: true) }
        pendingCompletion = true
        clock.play(); previousTime = nil; startLink(); render(); message = "Playing reconstructed sequence"
    }
    func pause() { tapClock?.suspend(); clock.pause(); invalidateLink(); render(); message = "Paused" }
    func restart() { guard ready else { return }; cancel(); pendingCompletion = true; frameIntervals.removeAll(keepingCapacity: true); clock.restart(); startLink(); render(); objectWillChange.send() }
    func stop() { cancel(); clock.stop(); render(); message = "Stopped" }
    func cancel() {
        invalidateLink(); tapClock = nil; clock.stop()
        if pendingCompletion { pendingCompletion = false; onCompletion?(.cancelled) }
        render(); objectWillChange.send()
    }
    func suspend() { if clock.state == .playing { pause(); message = "Paused while inactive · press Play to resume" } }
    func seek(_ time: Double) { if tapClock != nil { cancel() }; invalidateLink(); clock.seek(time); render(); objectWillChange.send() }
    private func startLink() {
        guard link == nil else { return }
        let target = CrystalTick(); target.owner = self; self.target = target
        let link = CADisplayLink(target: target,selector: #selector(CrystalTick.step(_:)))
        link.preferredFrameRateRange = CAFrameRateRange(minimum: 30,maximum: 60,preferred: 60)
        link.add(to: .main,forMode: .common); self.link = link
        view.isPlaying = true; view.rendersContinuously = true
    }
    private func invalidateLink() {
        link?.invalidate(); link = nil; target = nil; previousTime = nil
        view.isPlaying = false; view.rendersContinuously = false
    }
    fileprivate func tick(_ timestamp: CFTimeInterval) {
        let rawDelta = previousTime.map { max(0,timestamp-$0) } ?? 0
        if rawDelta > 0 { if frameIntervals.count >= 1024 { frameIntervals.removeFirst() }; frameIntervals.append(rawDelta) }
        let delta = min(0.1,rawDelta)
        previousTime = timestamp; callbackCount += 1
        let priorPhase = tapClock?.phase
        let ended: Bool
        if tapClock != nil { ended = tapClock!.advance(delta*(clock.speed.isFinite ? max(0.25,min(2,clock.speed)) : 1)) } else { ended = clock.advance(delta) }
        render()
        if callbackCount % 6 == 0 || ended || priorPhase != tapClock?.phase { objectWillChange.send() }
        if ended {
            invalidateLink(); message = "Reveal ready · no summon transaction"
            if pendingCompletion { pendingCompletion = false; onCompletion?(.finished) }
        }
    }
    // A deterministic pose function also supports static inspection and test captures.
    private func render() {
        guard ready || scene != nil else { return }
        let t = tapClock?.sourceTime ?? clock.time
        let p = CrystalPose.sample(t)
        let motion = tapClock?.motionTime ?? t
        SCNTransaction.begin(); SCNTransaction.animationDuration = 0; SCNTransaction.disableActions = true
        crystal.scale = SCNVector3(p.scale,p.scale,p.scale); crystal.position.y = Float(tapClock == nil ? p.lift : (1-(p.scale-0.28)/0.72)*8+sin(motion*2.4)*0.25)
        crystal.eulerAngles = SCNVector3(0,tapClock == nil ? p.turn : sin(motion*0.9)*0.12,0)
        let falling = tapClock?.phase == .fallingCrystals
        let entrance = tapClock?.includesFalling == true
        let fallTime = tapClock?.elapsed ?? 0
        var opacity = p.opacity
        if falling {
            // The existing main crystal is the final entrant: no duplicate hero mesh.
            let raw = max(0,min(1,(fallTime-(CrystalEntranceTiming.fallingDuration-CrystalEntranceTiming.heroLead))/CrystalEntranceTiming.heroLead))
            let eased = raw*raw*(3-2*raw)
            crystal.scale = SCNVector3(0.28*CrystalEntranceTiming.fallingWidth,0.28,0.28*CrystalEntranceTiming.fallingWidth)
            crystal.position.y = Float(8+(1-eased)*24+sin(motion*2.4)*0.25)
            opacity = raw*0.45
        } else if entrance && tapClock?.phase == .arriving {
            opacity = 0.45+0.55*p.opacity
            let width = 1+(CrystalEntranceTiming.fallingWidth-1)*(1-(p.scale-0.28)/0.72)
            crystal.scale = SCNVector3(p.scale*width,p.scale,p.scale*width)
        }
        fallingRoot.isHidden = !falling || clock.state == .stopped
        for (index,node) in fallers.enumerated() {
            let pose = FallingCrystalPose.sample(index: index,time: fallTime)
            node.isHidden = !falling || !pose.visible; node.opacity = pose.opacity
            node.position = SCNVector3(pose.x,pose.y,pose.z); node.scale = SCNVector3(pose.scale*CrystalEntranceTiming.fallingWidth,pose.scale,pose.scale*CrystalEntranceTiming.fallingWidth)
            node.eulerAngles = SCNVector3(0,sin(motion+Double(index))*0.18,pose.roll)
        }
        cloud.isHidden = !falling
        cloud.opacity = falling ? min(0.9,max(0,(CrystalEntranceTiming.fallingDuration-fallTime)/0.65)) : 0
        cloud.geometry?.firstMaterial?.diffuse.contentsTransform = SCNMatrix4MakeTranslation(Float(sin(motion*0.3)*0.03),Float((-motion*0.10).truncatingRemainder(dividingBy: 1)),0)
        let hidden = clock.state == .stopped || clock.state == .finished || tapClock?.phase == .finished || (falling && opacity == 0)
        crystal.isHidden = hidden
        let breaking = p.opening > 0.035
        base.isHidden = !baseVisible || breaking; gloss.isHidden = !glossVisible || breaking
        highlights.isHidden = !highlightsVisible || breaking; partial.isHidden = !partialVisible || breaking
        base.opacity = 0.95*opacity; gloss.opacity = (appearance == .rainbow ? 0.1 : 0.24)*opacity; highlights.opacity = (appearance == .rainbow ? 0.07 : 0.19)*opacity; partial.opacity = 0.17*opacity
        gloss.geometry?.firstMaterial?.diffuse.contentsTransform = SCNMatrix4MakeTranslation(Float((motion*0.025).truncatingRemainder(dividingBy: 1)),Float((motion*0.04).truncatingRemainder(dividingBy: 1)),0)
        fragments.isHidden = !breaking || !baseVisible
        for (i,node) in pieces.enumerated() {
            let a = Double(i%6)/6*Double.pi*2
            let d = p.opening*11; let vertical = i>=6 ? 1.0 : -1.0
            node.position = SCNVector3(cos(a)*d,vertical*d*0.6,sin(a)*d)
            node.eulerAngles = SCNVector3(p.opening*vertical*0.4,p.opening*sin(a)*0.6,0)
            node.opacity = max(0,1-p.opening*1.2)
        }
        halo.position.y = entrance ? crystal.position.y : 0
        halo.isHidden = hidden || !glowVisible; beam.isHidden = hidden || !glowVisible
        halo.opacity = 0.58*opacity+0.5*p.flash; beam.opacity = 0.21*opacity
        burst.isHidden = hidden || !glowVisible; burst.opacity = p.flash*0.9
        for (i,node) in stars.enumerated() {
            let phase = Double(i)*2.399963
            let radius = 5.6+Double(i%5)*1.4 + p.opening*12
            let y = (Double(i)*1.71+motion*1.7).truncatingRemainder(dividingBy: 33)-16 + p.opening*sin(phase)*10
            node.position = SCNVector3(cos(phase+motion*0.12)*radius,y,6+sin(phase)*2)
            node.opacity = (0.25+0.55*abs(sin(phase+motion*1.3)))*opacity*min(1,max(0,(16-abs(y))/2))
            node.isHidden = hidden || !particlesVisible
            if appearance == .rainbow {
                node.geometry?.firstMaterial?.multiply.contents = UIColor(hue: CGFloat((Double(i)/28+motion*0.045).truncatingRemainder(dividingBy: 1)),saturation: 0.5,brightness: 1,alpha: 1)
            }
        }
        SCNTransaction.commit(); view.setNeedsDisplay()
    }
    func snapshot() -> UIImage { view.snapshot() }
    deinit { link?.invalidate() }
}

struct ReconstructedCrystalViewport: UIViewRepresentable {
    let controller: CrystalReconstructionController
    func makeUIView(context: Context) -> SCNView { controller.view }
    func updateUIView(_ view: SCNView,context: Context) {}
}
struct CrystalReconstructionPreview: View {
    @StateObject private var controller = CrystalReconstructionController()
    @Environment(\.scenePhase) private var phase
    @State private var speed = 1.0
    @State private var diagnostic = ""
    var body: some View {
        ScrollView {
            VStack(alignment: .leading,spacing: 12) {
                Text("FFBE crystal reconstruction").font(.title2.bold())
                Text("Original recovered geometry and textures. Materials, layer roles, timing, motion and break effect are reconstructed.").font(.caption).foregroundStyle(.secondary)
                Picker("Appearance",selection: $controller.appearance) { ForEach(CrystalAppearance.allCases) { Text($0.rawValue).tag($0) } }.pickerStyle(.segmented)
                ReconstructedCrystalViewport(controller: controller).overlay(alignment: .bottom) { CrystalTouchPrompt(controller: controller).padding(.bottom,10) }.frame(height: 370).clipShape(RoundedRectangle(cornerRadius: 12))
                Text(controller.message).font(.caption).accessibilityIdentifier("reconstruction-status")
                HStack {
                    Button("Play") { controller.play() }
                    Button("Pause") { controller.pause() }.disabled(controller.clock.state != .playing)
                    Button("Restart") { controller.restart() }
                    Button("Stop") { controller.stop() }
                }.buttonStyle(.bordered).disabled(!controller.ready)
                Text("Falling entrance · reconstructed paths and timing").font(.headline)
                HStack {
                    Button("Play / Restart entrance") { controller.startTapPresentation() }
                    Button("Resume entrance") { controller.resumeTapPresentation() }
                }.buttonStyle(.bordered).disabled(!controller.ready)
                HStack {
                    Button("Inspect TOUCH SCREEN") { controller.inspectTouchState() }
                    Button("Open manually") { controller.resumeTapPresentation(); controller.tapToBreak() }
                }.buttonStyle(.bordered).disabled(!controller.ready)
                Button("Compare old tap arrival") { controller.startTapPresentation(includeFalling: false) }.disabled(!controller.ready)
                Text("Recovered shared-effect TOUCH SCREEN artwork. Missing prompt uses reconstructed typography. No rewards are generated here.").font(.caption)
                Button("Inspect static appearance") { controller.inspect() }.disabled(!controller.ready)
                Text(String(format: "%@ · %@ · %.2f / %.2f s",controller.clock.state.rawValue,controller.stage,controller.clock.time,CrystalClock.duration)).font(.caption.monospaced())
                Slider(value: Binding(get: { controller.clock.time },set: { controller.seek($0) }),in: 0...CrystalClock.duration).disabled(!controller.ready)
                HStack { Text("Speed"); Slider(value: $speed,in: 0.25...2,step: 0.25); Text(String(format: "%.2f×",speed)) }.font(.caption)
                Toggle("Base surface",isOn: $controller.baseVisible)
                Toggle("Gloss overlay (reconstructed mapping)",isOn: $controller.glossVisible)
                Toggle("Facet highlights",isOn: $controller.highlightsVisible)
                Toggle("Glow and opening flash",isOn: $controller.glowVisible)
                Toggle("Particles",isOn: $controller.particlesVisible)
                Toggle("Inspect partial model 003 (role unknown)",isOn: $controller.partialVisible)
                Toggle("Compare original models 004 / 005",isOn: $controller.alternateModels)
                Text("Default: original models 001/002. Model002’s cloud texture is not supplied here; caustic texture glow_013 is an explicit reconstructed gloss override. Model003 is not identified as shards. Opening separates clusters of the original surface triangles.").font(.caption).foregroundStyle(.secondary)
                Text("No network, currency, inventory or reward operations. Inactive playback pauses; press Play to resume.").font(.caption)
                if !diagnostic.isEmpty { Text(diagnostic).font(.caption).accessibilityIdentifier("reconstruction-diagnostics") }
            }.padding()
        }.navigationTitle("Crystal reconstruction").preferredColorScheme(.dark)
            .task {
                controller.load()
                if ProcessInfo.processInfo.arguments.contains("--falling-crystal-diagnostics") { diagnostic = await CrystalEntranceDiagnostics.run(controller) }
                else if ProcessInfo.processInfo.arguments.contains("--crystal-reconstruction-diagnostics") { diagnostic = await CrystalReconstructionDiagnostics.run(controller) }
            }
            .onChange(of: speed) { controller.speed = $0 }
            .onChange(of: phase) { if $0 != .active { controller.suspend() } }
            .onDisappear { controller.stop() }
    }
}
