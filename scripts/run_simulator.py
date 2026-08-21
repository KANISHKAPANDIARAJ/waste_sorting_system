import sys
import os
import argparse
import time

# Add root folder to sys.path so we can import iot package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iot.simulator import IoTSimulator

def main():
    parser = argparse.ArgumentParser(description="IoT Waste Segregation Conveyor Simulator client.")
    parser.add_argument('--device', type=str, default='SIM-001', help='Simulated Device ID (default: SIM-001)')
    parser.add_argument('--interval', type=int, default=5, help='Telemetry reporting interval in seconds (default: 5)')
    parser.add_argument('--url', type=str, default='http://127.0.0.1:5000', help='Target Flask API Base URL (default: http://127.0.0.1:5000)')
    
    args = parser.parse_args()
    
    # Resolve samples directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    samples_dir = os.path.join(root_dir, 'uploads', 'waste', 'train_samples')
    
    simulator = IoTSimulator(
        device_id=args.device,
        base_url=args.url,
        interval=args.interval,
        samples_dir=samples_dir
    )
    
    try:
        simulator.start()
        # Keep main thread alive
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping simulator...")
        simulator.stop()
        print("Simulator shut down.")

if __name__ == '__main__':
    main()
