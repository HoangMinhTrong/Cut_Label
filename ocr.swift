import Foundation
import Vision
import ImageIO

struct Line: Codable {
    let text: String
    let confidence: Float
}
do {
    guard CommandLine.arguments.count == 2 else { throw NSError(domain: "Missing image", code: 1) }
    let url = URL(fileURLWithPath: CommandLine.arguments[1])
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["en-US"]
    request.usesLanguageCorrection = false
    request.minimumTextHeight = 0.002
    let handler = VNImageRequestHandler(url: url, options: [:])
    try handler.perform([request])
    let lines = (request.results ?? []).compactMap { item -> Line? in
        guard let result = item.topCandidates(1).first else { return nil }
        return Line(text: result.string, confidence: result.confidence)
    }
    FileHandle.standardOutput.write(try JSONEncoder().encode(lines))
} catch {
    FileHandle.standardError.write(Data("OCR: \(error)\n".utf8))
    exit(1)
}
