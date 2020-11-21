import asyncio
import uuid

class ListTargetGen:
	def __init__(self, targets):
		self.targets = targets
		self.total_cnt = 0

	async def run(self, target_q):
		try:
			for target in self.targets:
				self.total_cnt += 1
				target = target.strip()
				await target_q.put((str(uuid.uuid4()),target))
				await asyncio.sleep(0)
			return self.total_cnt, None
		except Exception as e:
			return self.total_cnt, e

	async def get_all(self):
		try:
			for line in self.targets:
				self.total_cnt += 1
				line = line.strip()
				if line == '':
					continue
				yield str(uuid.uuid4()), line, None
				await asyncio.sleep(0)
				self.total_cnt += 1
		except Exception as e:
			yield None, None, e