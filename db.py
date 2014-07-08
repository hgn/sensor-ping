import os

class DB:

	FILE_PATH = "/tmp/foo.db"

	@staticmethod
	def append_data(data):
		file = open(DB.FILE_PATH, 'a+')
		file.write("%s\n" % (data))
		file.close()

	def get_data(data):
		if not os.path.isfile(DB.FILE_PATH):
			return None
		file = open(DB.FILE_PATH, 'r')
		lines = file.readlines()
		file.close()
		return lines


	def reset():
		if os.path.isfile(DB.FILE_PATH):
			os.remove(DB.FILE_PATH)
		else:
			 print("Error: %s file not found" % DB.FILE_PATH)


