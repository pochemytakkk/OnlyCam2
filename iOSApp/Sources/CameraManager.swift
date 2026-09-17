import AVFoundation
import Network
import UIKit

class CameraManager: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    var captureSession: AVCaptureSession!
    var connection: NWConnection?
    
    func start() {
        setupNetwork()
        setupCamera()
    }
    
    func setupNetwork() {
        // 127.0.0.1 используется для подключения по USB-кабелю
        let host = NWEndpoint.Host("127.0.0.1")
        let port = NWEndpoint.Port(integerLiteral: 8080)
        
        connection = NWConnection(host: host, port: port, using: .tcp)
        connection?.start(queue: .global())
    }
    
    func setupCamera() {
        captureSession = AVCaptureSession()
        captureSession.sessionPreset = .hd1280x720
        
        // Запрашиваем сверхширокоугольный объектив 0.5x
        guard let videoDevice = AVCaptureDevice.default(.builtInUltraWideCamera, for: .video, position: .back),
              let videoDeviceInput = try? AVCaptureDeviceInput(device: videoDevice),
              captureSession.canAddInput(videoDeviceInput) else {
            print("Сверхширокоугольная камера не найдена")
            return
        }
        captureSession.addInput(videoDeviceInput)
        
        let videoOutput = AVCaptureVideoDataOutput()
        videoOutput.setSampleBufferDelegate(self, queue: DispatchQueue(label: "videoQueue"))
        if captureSession.canAddOutput(videoOutput) {
            captureSession.addOutput(videoOutput)
        }
        
        DispatchQueue.global().async {
            self.captureSession.startRunning()
        }
    }
    
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let ciImage = CIImage(cvPixelBuffer: imageBuffer)
        let context = CIContext()
        
        if let cgImage = context.createCGImage(ciImage, from: ciImage.extent) {
            let uiImage = UIImage(cgImage: cgImage)
            // Сжимаем кадр, чтобы видео передавалось без задержек
            if let jpegData = uiImage.jpegData(compressionQuality: 0.6) {
                sendData(data: jpegData)
            }
        }
    }
    
    func sendData(data: Data) {
        var size = UInt32(data.count).bigEndian
        let sizeData = Data(bytes: &size, count: MemoryLayout<UInt32>.size)
        
        self.connection?.send(content: sizeData, completion: .contentProcessed({ _ in }))
        self.connection?.send(content: data, completion: .contentProcessed({ _ in }))
    }
}