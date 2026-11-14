// Probe 3: Apple's built-in SoundAnalysis classifier (303 classes) as a zero-shot baseline.
// Prints one JSON line per input file: {"file": ..., "seconds": ..., "windows": n, "mean": {class: mean confidence}}
// Build: swiftc -O apple_classify.swift -o apple_classify   Run: ./apple_classify a.wav b.wav ...
import Foundation
import SoundAnalysis
import AVFoundation

final class Collector: NSObject, SNResultsObserving {
    var sums: [String: Double] = [:]
    var windows = 0
    func request(_ request: SNRequest, didProduce result: SNResult) {
        guard let r = result as? SNClassificationResult else { return }
        windows += 1
        for c in r.classifications { sums[c.identifier, default: 0] += c.confidence }
    }
}

let request = try SNClassifySoundRequest(classifierIdentifier: .version1)
for path in CommandLine.arguments.dropFirst() {
    let t0 = Date()
    let analyzer = try SNAudioFileAnalyzer(url: URL(fileURLWithPath: path))
    let col = Collector()
    try analyzer.add(request, withObserver: col)
    analyzer.analyze()
    let n = Double(max(col.windows, 1))
    let mean = col.sums.mapValues { ($0 / n * 10000).rounded() / 10000 }
    let out: [String: Any] = ["file": (path as NSString).lastPathComponent,
                              "seconds": Date().timeIntervalSince(t0), "windows": col.windows, "mean": mean]
    let data = try JSONSerialization.data(withJSONObject: out)
    print(String(data: data, encoding: .utf8)!)
}
