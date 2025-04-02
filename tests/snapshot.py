import numpy as np
import matplotlib.pyplot as plt

from scopebind.device import Device


# Function to perform FFT and return frequencies and magnitudes
def perform_fft(data: np.ndarray, sampling_rate: float) -> np.ndarray:
    N = len(data)
    fft_result = np.fft.fft(data)
    fft_freqs = np.fft.fftfreq(N, d=1 / sampling_rate)
    fft_magnitudes = np.abs(fft_result)[:N // 2]
    fft_freqs = fft_freqs[:N // 2]
    return fft_freqs, fft_magnitudes


if __name__ == "__main__":

    sampling_rate = 4000000  # supported: [1000000, 4000000, 8000000, 16000000, 48000000]


    # Setup the oscilloscope device connection
    scope = Device()
    scope.start()  # Connect to the device

    # Read some data (assuming data is raw signal data in bytes)
    raw_data = scope.read(1024*1024)  # Reading  bytes of data

    scope.stop()

    # Assuming the data is a simple byte array, we'll convert it to a numpy array
    signal = np.array(raw_data, dtype=np.float32)

    # Plot the first 200 samples as a time-domain signal
    plt.figure(figsize=(12, 6))

    # Time plot (assuming the signal is sampled at 1kHz)
    time = np.arange(len(signal))  # Time array (in samples)
    plt.subplot(2, 1, 1)
    plt.plot(time[:200], signal[:200], label="Signal (First 200 samples)")
    plt.title("Time Domain Signal (First 200 Samples)")
    plt.xlabel("Time (samples)")
    plt.ylabel("Amplitude")
    plt.legend()

    # Perform and plot the FFT
    fft_freqs, fft_magnitudes = perform_fft(signal, sampling_rate)

    plt.subplot(2, 1, 2)
    plt.plot(fft_freqs, fft_magnitudes, label="FFT Magnitude", color='orange')
    plt.title("FFT of the Signal")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")
    plt.legend()

    # Show the plots
    plt.tight_layout()
    plt.show()
