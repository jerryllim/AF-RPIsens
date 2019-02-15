import NetworkManager

network_manager = NetworkManager.NetworkManager()

while True:
	jam = input("option 1: jam\n")
	if jam == "1":
		network_manager.request_jam()
	else:
		print("no such commands")