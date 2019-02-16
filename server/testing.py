import sys
import NetworkManager

network_manager = NetworkManager.NetworkManager()

try:
	while True:
		jam = input("\noption 1: jam\noption 2: exit\nplease enter the option no.\n")
		if jam == "1":
			print("requesting...")
			network_manager.request_jam()
		elif:
			print("exiting...")
			break
		else:
			print("no such commands")
except KeyboardInterrupt:
	print("interrupted with ctrl+c")
	raise
finally:
	sys.exit()