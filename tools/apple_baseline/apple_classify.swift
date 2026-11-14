// Apple's built-in SoundAnalysis classifier (SNClassifySoundRequest .version1, 303 classes) as a zero-shot baseline.
// Reads channel 0 of each audio file into memory and prints one JSON line per file:
//   {"file": name, "windows": n, "mean": {class: mean confidence over the windows}}
// Build: ./build.sh    Run: ./apple_classify a.flac b.flac ...   (macOS only)
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
    do {
        let file = try AVAudioFile(forReading: URL(fileURLWithPath: path))
        let inFmt = file.processingFormat
        guard let all = AVAudioPCMBuffer(pcmFormat: inFmt, frameCapacity: AVAudioFrameCount(file.length)) else { continue }
        try file.read(into: all)
        let mono = AVAudioFormat(standardFormatWithSampleRate: inFmt.sampleRate, channels: 1)!
        let buf = AVAudioPCMBuffer(pcmFormat: mono, frameCapacity: all.frameLength)!
        buf.frameLength = all.frameLength
        memcpy(buf.floatChannelData![0], all.floatChannelData![0], Int(all.frameLength) * MemoryLayout<Float>.size)
        let analyzer = SNAudioStreamAnalyzer(format: mono)
        let col = Collector()
        try analyzer.add(request, withObserver: col)
        analyzer.analyze(buf, atAudioFramePosition: 0)
        analyzer.completeAnalysis()
        let n = Double(max(col.windows, 1))
        let mean = col.sums.mapValues { ($0 / n * 10000).rounded() / 10000 }
        let out: [String: Any] = ["file": (path as NSString).lastPathComponent, "windows": col.windows, "mean": mean]
        print(String(data: try JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
    } catch {
        print("{\"file\": \"\((path as NSString).lastPathComponent)\", \"error\": \"\(error.localizedDescription)\"}")
    }
}
