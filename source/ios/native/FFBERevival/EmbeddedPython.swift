import Foundation

private struct PythonEnvelope<T: Decodable>: Decodable {
    let ok: Bool
    let value: T?
    let error: ServerFailure.Detail?
}
struct PythonProof: Decodable {
    let message: String
    let version: String
    let platform: String
    let answer: Int
}

// One interpreter and one serial worker, shared by every local backend instance.
// No CPython symbols or objects escape this boundary.
final class PythonWorker {
    static let shared = PythonWorker()
    private let queue = DispatchQueue(label: "ffbe.embedded-python", qos: .userInitiated)
    private init() {}

    func call<T: Decodable>(_ request: [String: String], as type: T.Type = T.self) async throws -> T {
        let requestData = try JSONEncoder().encode(request)
        let requestText = String(decoding: requestData, as: UTF8.self)
        return try await withCheckedThrowingContinuation { continuation in
            queue.async {
                do {
                    guard let resources = Bundle.main.resourcePath else {
                        throw APIError(message: "Application resources are missing")
                    }
                    let text = try PythonBridge.call(requestText, resources: resources)
                    let response = try JSONDecoder().decode(PythonEnvelope<T>.self, from: Data(text.utf8))
                    guard response.ok, let value = response.value else {
                        throw APIError(message: response.error?.message ?? "Embedded Python returned no result", code: response.error?.code)
                    }
                    continuation.resume(returning: value)
                } catch {
                    continuation.resume(throwing: error)
                }
            }
        }
    }
}

private struct PythonReady: Decodable { let ready: Bool; let network_disabled: Bool }

actor EmbeddedSummonBackend: SummonBackend {
    static let shared = EmbeddedSummonBackend()
    private let storageOverride: URL?
    private var initialized = false

    // A separate root is reserved for explicit diagnostics launches.
    init(storage: URL? = nil) { storageOverride = storage }

    private func initialize() async throws {
        if initialized { return }
        let manager = FileManager.default
        let storage: URL
        if let override = storageOverride {
            storage = override
        } else {
            storage = try manager.url(for: .applicationSupportDirectory, in: .userDomainMask,
                                      appropriateFor: nil, create: true)
                .appendingPathComponent("FFBERevival/offline-demo-v1", isDirectory: true)
        }
        try manager.createDirectory(at: storage, withIntermediateDirectories: true)
        #if os(iOS)
        try manager.setAttributes([.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
                                  ofItemAtPath: storage.path)
        #endif
        guard let resources = Bundle.main.resourceURL else {
            throw APIError(message: "Bundled Python metadata is missing")
        }
        let data = resources.appendingPathComponent("PythonApp/metadata/demo", isDirectory: true)
        let response: PythonReady = try await PythonWorker.shared.call([
            "operation": "initialize", "data": data.path, "storage": storage.path
        ])
        guard response.ready && response.network_disabled else {
            throw APIError(message: "Offline backend initialization did not complete")
        }
        initialized = true
    }
    func banners() async throws -> BannersResponse {
        try await initialize()
        return try await PythonWorker.shared.call(["operation": "banners"])
    }
    func state() async throws -> Campaign {
        try await initialize()
        return try await PythonWorker.shared.call(["operation": "state"])
    }
    func developerAddLapis(amount: Int) async throws -> Campaign {
        try await initialize()
        return try await PythonWorker.shared.call(["operation": "developer_add_lapis", "amount": String(amount)])
    }
    func summon(bannerID: String, offer: String) async throws -> SummonResponse {
        try await initialize()
        return try await PythonWorker.shared.call(["operation": "summon", "banner_id": bannerID, "offer": offer])
    }
}
