import asyncio
import uuid

class FileTargetGen:
	def __init__(self, filename):
		self.filename = filename
		self.total_cnt = 0

	async def run(self, target_q):
		try:
			self.total_cnt = 0
			with open(self.filename, 'r') as f:
				for line in f:
					line = line.strip()
					if line == '':
						continue
					await target_q.put((str(uuid.uuid4()), line))
					await asyncio.sleep(0)
					self.total_cnt += 1
			return self.total_cnt, None
		except Exception as e:
			return self.total_cnt, e

	async def get_all(self):
		try:
			with open(self.filename, 'r') as f:
				for line in f:
					line = line.strip()
					if line == '':
						continue
					yield str(uuid.uuid4()), line, None
					await asyncio.sleep(0)
					self.total_cnt += 1
		except Exception as e:
			yield None, None, e