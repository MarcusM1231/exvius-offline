import SwiftUI
import SceneKit
import CryptoKit
import Darwin

private struct CrystalMesh: Decodable {
    let schema: Int
    let vertices: Int
    let triangles: Int
    let positions: [Float]
    let normals: [Float]
    let uvs: [Float]
    let indices: [UInt32]
    let vertex_colors_raw: [UInt32]
}
private struct CrystalReceipt: Decodable { let files: [String: String] }
private struct CrystalFailure: LocalizedError {
    let message: String
    var errorDescription: String? { message }
}
private final class CrystalFrameMeter: NSObject, SCNSceneRendererDelegate {
    private let lock = NSLock()
    private var count = 0
    func renderer(_ renderer: SCNSceneRenderer, updateAtTime time: TimeInterval) {
        lock.lock(); count += 1; lock.unlock()
    }
    var frames: Int { lock.lock(); defer { lock.unlock() }; return count }
}

@MainActor
final class CrystalInspection: ObservableObject {
    @Published private(set) var status = "Loading recovered mesh…"
    @Published private(set) var ready = false
    @Published private(set) var running = false
    let view = SCNView(frame: .zero)
    private let meter = CrystalFrameMeter()
    private var model: SCNNode?
    private var camera: SCNNode?
    private var scene: SCNScene?
    private var directory: URL?
    private(set) var vertexCount = 0
    private(set) var triangleCount = 0
    private(set) var resourceBytes = 0
    private(set) var geometryBytes = 0
    var renderCallbacks: Int { meter.frames }

    static func resourceDirectory() -> URL? {
        Bundle.main.resourceURL?.appendingPathComponent(ProcessInfo.processInfo.arguments.contains("--crystal-assets-missing") ? "CrystalPreview-Missing" : "CrystalPreview")
    }
    func load(directory: URL? = nil) {
        let directory = directory ?? Self.resourceDirectory()
        stop()
        ready = false
        self.directory = directory
        do {
            guard let directory else { throw CrystalFailure(message: "Crystal resources are missing") }
            let receipt = try JSONDecoder().decode(CrystalReceipt.self, from: Data(contentsOf: directory.appendingPathComponent("receipt.json")))
            guard Set(receipt.files.keys) == Set(["mesh.json","texture.png","catalog.json"]) else { throw CrystalFailure(message: "Unexpected crystal content") }
            var blobs: [String: Data] = [:]
            for (name, expected) in receipt.files {
                let data = try Data(contentsOf: directory.appendingPathComponent(name))
                guard data.count < 4*1024*1024,
                      SHA256.hash(data: data).map({ String(format: "%02x", $0) }).joined() == expected else {
                    throw CrystalFailure(message: "Crystal content checksum failed")
                }
                blobs[name] = data
            }
            guard let meshData = blobs["mesh.json"], let textureData = blobs["texture.png"],
                  let image = UIImage(data: textureData) else { throw CrystalFailure(message: "Crystal texture did not decode") }
            let mesh = try JSONDecoder().decode(CrystalMesh.self, from: meshData)
            guard mesh.schema == 1, mesh.vertices > 0, mesh.vertices <= 100000, mesh.triangles > 0,
                  mesh.positions.count == mesh.vertices*3, mesh.normals.count == mesh.vertices*3,
                  mesh.uvs.count == mesh.vertices*2, mesh.vertex_colors_raw.count == mesh.vertices, mesh.indices.count == mesh.triangles*3,
                  mesh.indices.allSatisfy({ $0 < UInt32(mesh.vertices) }),
                  mesh.positions.allSatisfy(\.isFinite), mesh.normals.allSatisfy(\.isFinite), mesh.uvs.allSatisfy(\.isFinite) else {
                throw CrystalFailure(message: "Invalid crystal mesh buffers")
            }
            let positions = stride(from: 0,to: mesh.positions.count,by: 3).map { SCNVector3(mesh.positions[$0],mesh.positions[$0+1],mesh.positions[$0+2]) }
            let normals = stride(from: 0,to: mesh.normals.count,by: 3).map { SCNVector3(mesh.normals[$0],mesh.normals[$0+1],mesh.normals[$0+2]) }
            let uv = stride(from: 0,to: mesh.uvs.count,by: 2).map { CGPoint(x: CGFloat(mesh.uvs[$0]),y: CGFloat(mesh.uvs[$0+1])) }
            // Preserve packed per-vertex values as normalized RGBA for inspection.
            // This conventional mapping is diagnostic: original BISHAMON material
            // and shader interpretation remains unverified; raw words are retained.
            let colors: [Float] = mesh.vertex_colors_raw.flatMap { word in
                (0..<4).map { Float((word >> ($0*8)) & 255) / 255 }
            }
            let colorData = colors.withUnsafeBufferPointer { Data(buffer: $0) }
            let colorSource = SCNGeometrySource(data: colorData,semantic: .color,vectorCount: mesh.vertices,
                usesFloatComponents: true,componentsPerVector: 4,bytesPerComponent: 4,dataOffset: 0,dataStride: 16)
            let indices = mesh.indices.withUnsafeBufferPointer { Data(buffer: $0) }
            let geometry = SCNGeometry(sources: [SCNGeometrySource(vertices: positions),SCNGeometrySource(normals: normals),SCNGeometrySource(textureCoordinates: uv), colorSource],
                elements: [SCNGeometryElement(data: indices,primitiveType: .triangles,primitiveCount: mesh.triangles,bytesPerIndex: 4)])
            let material = SCNMaterial()
            material.diffuse.contents = image
            material.lightingModel = .lambert
            material.isDoubleSided = true
            geometry.materials = [material]
            geometryBytes = geometry.sources.reduce(0) { $0+$1.data.count } + indices.count
            let scene = SCNScene()
            let node = SCNNode(geometry: geometry)
            scene.rootNode.addChildNode(node)
            let camera = SCNNode()
            camera.camera = SCNCamera()
            camera.camera?.usesOrthographicProjection = true
            camera.camera?.orthographicScale = 17
            camera.camera?.zNear = 0.1
            camera.camera?.zFar = 200
            scene.rootNode.addChildNode(camera)
            let ambient = SCNNode(); ambient.light = SCNLight(); ambient.light?.type = .ambient; ambient.light?.intensity = 350
            scene.rootNode.addChildNode(ambient)
            let light = SCNNode(); light.light = SCNLight(); light.light?.type = .directional; light.light?.intensity = 750
            light.eulerAngles = SCNVector3(-0.45,-0.6,0); scene.rootNode.addChildNode(light)
            self.scene = scene; model = node; self.camera = camera
            view.scene = scene; view.pointOfView = camera; view.delegate = meter
            view.backgroundColor = UIColor(red: 0.025,green: 0.04,blue: 0.08,alpha: 1)
            view.allowsCameraControl = true; view.defaultCameraController.inertiaEnabled = false
            view.antialiasingMode = .multisampling4X
            view.preferredFramesPerSecond = 30 // Diagnostic viewport cap, not recovered animation timing.
            vertexCount = mesh.vertices; triangleCount = mesh.triangles
            resourceBytes = blobs.values.reduce(0) { $0+$1.count }
            ready = true
            restart()
        } catch {
            scene = nil; model = nil; camera = nil; view.scene = nil
            status = "Preview unavailable: " + error.localizedDescription
        }
    }
    func show() {
        guard ready else { return }
        model?.isHidden = false; scene?.isPaused = true
        view.rendersContinuously = false; view.isPlaying = false; running = true
        view.setNeedsDisplay()
        status = "Original mesh + texture · diagnostic lighting/camera"
    }
    func restart() {
        guard ready else { return }
        camera?.position = SCNVector3(0,1.06,45)
        camera?.look(at: SCNVector3(0,1.06,0))
        view.pointOfView = camera
        show()
    }
    func stop() {
        view.isPlaying = false; view.rendersContinuously = false; scene?.isPaused = true
        model?.isHidden = true; running = false
        if ready { status = "Stopped · no animation timeline has been recovered" }
    }
    func suspend() { view.isPlaying = false; view.rendersContinuously = false; scene?.isPaused = true }
    func resume() { if running { show() } }
    func beginViewportBenchmark() { scene?.isPaused = false; view.rendersContinuously = true; view.isPlaying = true }
    func snapshot() -> UIImage { view.snapshot() }
    static func residentBytes() -> UInt64 {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size / MemoryLayout<natural_t>.size)
        let result = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self,capacity: Int(count)) {
                task_info(mach_task_self_,task_flavor_t(MACH_TASK_BASIC_INFO),$0,&count)
            }
        }
        return result == KERN_SUCCESS ? UInt64(info.resident_size) : 0
    }
}

private struct CrystalViewport: UIViewRepresentable {
    @ObservedObject var inspection: CrystalInspection
    func makeUIView(context: Context) -> SCNView { inspection.view }
    func updateUIView(_ view: SCNView,context: Context) {}
}

struct CrystalPreview: View {
    @StateObject private var inspection = CrystalInspection()
    @State private var diagnostics = ""
    @Environment(\.scenePhase) private var phase
    var body: some View {
        ScrollView {
            VStack(alignment: .leading,spacing: 15) {
                NavigationLink("Open animated crystal reconstruction") { CrystalReconstructionPreview() }
                Text("Original mesh diagnostic").font(.title2.bold())
                Text("This is not recovered crystal-animation playback. Geometry, normals, UVs and texture are recovered; camera and lighting are diagnostic.")
                    .font(.callout).foregroundStyle(.secondary)
                CrystalViewport(inspection: inspection).frame(height: 360).clipShape(RoundedRectangle(cornerRadius: 12))
                Text(inspection.status).font(.caption).accessibilityIdentifier("crystal-preview-status")
                HStack {
                    Button("Show mesh") { inspection.show() }.disabled(!inspection.ready || inspection.running)
                    Button("Restart view") { inspection.restart() }.disabled(!inspection.ready)
                    Button("Stop") { inspection.stop() }.disabled(!inspection.running)
                }.buttonStyle(.bordered)
                Button("Play original animation — unavailable") {}.disabled(true)
                Text("Drag to inspect the model. No automatic motion, blue tint, crystal upgrade or breaking sequence is invented here.").font(.caption)
                Text("\(inspection.vertexCount) vertices · \(inspection.triangleCount) triangles · local resources only").font(.caption.monospaced())
                if !diagnostics.isEmpty { Text(diagnostics).font(.caption).accessibilityIdentifier("crystal-diagnostics") }
            }.padding()
        }.navigationTitle("Crystal recovery").preferredColorScheme(.dark)
            .task {
                inspection.load()
                if ProcessInfo.processInfo.arguments.contains("--crystal-diagnostics") { diagnostics = await check() }
            }
            .onChange(of: phase) { value in if value == .active { inspection.resume() } else { inspection.suspend() } }
            .onDisappear { inspection.stop() }
    }
    @MainActor private func check() async -> String {
        var report: [String: Any] = [:]
        do {
            guard inspection.ready, inspection.vertexCount == 960, inspection.triangleCount == 320 else { throw CrystalFailure(message: "Original mesh did not load") }
            for _ in 0..<3 {
                inspection.stop(); guard !inspection.running else { throw CrystalFailure(message: "Stop failed") }
                inspection.restart(); guard inspection.running else { throw CrystalFailure(message: "Restart failed") }
            }
            inspection.suspend()
            guard !inspection.view.isPlaying else { throw CrystalFailure(message: "Suspend failed") }
            inspection.resume()
            _ = inspection.snapshot() // Compile/warm the real mesh/material before measuring.
            inspection.beginViewportBenchmark()
            try await Task.sleep(nanoseconds: 2_000_000_000)
            inspection.beginViewportBenchmark() // Reassert after initial scene activation/resume.
            let beforeFrames = inspection.renderCallbacks
            let before = ProcessInfo.processInfo.systemUptime
            try await Task.sleep(nanoseconds: 2_000_000_000)
            let elapsed = ProcessInfo.processInfo.systemUptime-before
            let callbacks = inspection.renderCallbacks-beforeFrames
            inspection.suspend()
            let image = inspection.snapshot()
            inspection.stop(); inspection.restart()
            let repeated = inspection.snapshot()
            var snapshotMilliseconds: [Double] = []
            for _ in 0..<8 {
                let start = ProcessInfo.processInfo.systemUptime
                _ = inspection.snapshot()
                snapshotMilliseconds.append((ProcessInfo.processInfo.systemUptime-start)*1000)
            }
            let repeatable = image.pngData() == repeated.pngData()
            guard image.size.width > 0,image.size.height > 0 else { throw CrystalFailure(message: "Rendered frame missing") }
            let missing = CrystalInspection()
            missing.load(directory: Bundle.main.resourceURL?.appendingPathComponent("absent-crystal-test"))
            guard !missing.ready else { throw CrystalFailure(message: "Missing resource accepted") }
            let scratch = FileManager.default.temporaryDirectory.appendingPathComponent("crystal-corrupt-" + UUID().uuidString)
            guard let original = CrystalInspection.resourceDirectory() else { throw CrystalFailure(message: "Missing test inputs") }
            try FileManager.default.copyItem(at: original,to: scratch)
            defer { try? FileManager.default.removeItem(at: scratch) }
            try Data("corrupt diagnostic input".utf8).write(to: scratch.appendingPathComponent("mesh.json"))
            let corrupt = CrystalInspection(); corrupt.load(directory: scratch)
            guard !corrupt.ready else { throw CrystalFailure(message: "Corrupted mesh accepted") }
            report = ["status":"passed","vertices":inspection.vertexCount,"triangles":inspection.triangleCount,
                      "repeatable_inspection":true,"stop_restart":true,"suspend_resume_handler":true,"missing_resources_rejected":true,"corrupt_resources_rejected":true,
                      "resident_memory_bytes":CrystalInspection.residentBytes(),"resource_bytes":inspection.resourceBytes,"geometry_source_and_index_bytes":inspection.geometryBytes,
                      "repeatable_snapshot_bytes":repeatable,"normal_preview_continuous_rendering":false,
                      "viewport_render_callbacks_per_second":Double(callbacks)/elapsed,"viewport_cap_fps":30,
                      "snapshot_median_ms":snapshotMilliseconds.sorted()[4],"snapshot_samples":8,
                      "view_has_window":inspection.view.window != nil,"application_state_raw":UIApplication.shared.applicationState.rawValue,
                      "fps_scope":"static viewport callbacks; not recovered animation FPS",
                      "original_animation_recovered":false,"backend_isolation":"direct preview route; no backend APIs in preview",
                      "network_design":"local bundle resources only","normal_campaign_accessed":false]
            let folder = try FileManager.default.url(for: .applicationSupportDirectory,in: .userDomainMask,appropriateFor: nil,create: true)
                .appendingPathComponent("FFBERevival/validation",isDirectory: true)
            try FileManager.default.createDirectory(at: folder,withIntermediateDirectories: true)
            try image.pngData()?.write(to: folder.appendingPathComponent("crystal-mesh-frame.png"),options: .atomic)
            try repeated.pngData()?.write(to: folder.appendingPathComponent("crystal-mesh-restarted.png"),options: .atomic)
        } catch { report = ["status":"failed","error":error.localizedDescription,"original_animation_recovered":false] }
        do {
            let folder = try FileManager.default.url(for: .applicationSupportDirectory,in: .userDomainMask,appropriateFor: nil,create: true).appendingPathComponent("FFBERevival/validation",isDirectory: true)
            try FileManager.default.createDirectory(at: folder,withIntermediateDirectories: true)
            try JSONSerialization.data(withJSONObject: report,options: [.prettyPrinted,.sortedKeys]).write(to: folder.appendingPathComponent("crystal-report.json"),options: .atomic)
        } catch { return "Could not write diagnostic report" }
        return String(describing: report["status"] ?? "failed")
    }
}
