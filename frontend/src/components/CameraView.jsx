export default function CameraView({ videoRef, canvasRef, cameraStatus, cameraError }) {
  return (
    <div className="camera-wrap">
      <video ref={videoRef} className="camera-video" muted playsInline />
      <canvas ref={canvasRef} className="camera-overlay" />
      {cameraStatus === "loading" && <div className="camera-message">Loading camera...</div>}
      {cameraStatus === "error" && (
        <div className="camera-message error">
          Camera failed: {cameraError || "unknown error"}
          <br />
          (On non-localhost addresses, enable the Chrome insecure-origin flag.)
        </div>
      )}
    </div>
  );
}