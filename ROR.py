from datetime import datetime, timedelta
import csv
import urllib
import matplotlib.pyplot as plt
import numpy as np


class Share:
	"""Store the prices for the share"""
	shareprices = []

	def __init__(self, ticker, start_date):
		"""Load share prices into the object"""
		self.shareprices = self.fetch_share_price(ticker, start_date)
	
	def get_price(self, date):
		"""Get the price on the share on the supplied date"""
		for offset in range(60):
			d = date - timedelta(days=offset)
			datestr = '{0}-{1:02}-{2:02}'.format(d.year, d.month, d.day)
			line = [i for i in self.shareprices if i['Date'] == datestr]
			if len(line) == 1:
				return float(line[0]['Close']) / 100
		print 'No suitable value found for ', date
	
	def fetch_share_price(self, ticker, early_date):
		"""Fetch the share price for ticker from early_date to the present"""
		# MIDD.L from
		# 30-Mar-2004 to
		# 21-Jun-2011
		# http://ichart.finance.yahoo.com/table.csv?s=MIDD.L&d=5&e=21&f=2011&g=d&a=2&b=30&c=2004&ignore=.csv
		
		filename = ticker + '.csv' 
		f = open(filename, 'r')
		c = csv.DictReader(f)
		l = []
		for i in c:
			l.append(i)
		return l
	
class Account:
	"""Maintain a record of the current state of the account"""

	units = 0
	cash = 0.
	portfolio = {}
	contributions = 0.
	# Expected format: {'ticker':{'num':n, 'obj':Share object}, ... }

	def buy(self, ticker, num, price, dealing_fee, date):
		"""Buy a share"""
		self.cash -= float(num) * float(price)
		if dealing_fee:
			self.cash -= float(dealing_fee)
		if ticker in self.portfolio:
			self.portfolio[ticker]['num'] += float(num)
		else:
			self.portfolio[ticker] = {'num':float(num), 'obj':Share(ticker, date)}
	
	def sell(self, ticker, num, price, dealing_fee):
		"""Sell a share"""
		self.portfolio[ticker]['num'] -= float(num)
		self.cash += float(num) * float(price)
		if dealing_fee:
			self.cash -= float(dealing_fee)
	
	def dividend(self, ticker, total_value):
		"""Record the receipt of a dividend"""
		self.cash += float(total_value)
	
	def add_money(self, amount, date):
		"""Record a contribution to the account"""
		unit_value = self.get_unit_value(date)
		units = float(amount) / unit_value
		self.units += units
		self.cash += float(amount)
		self.contributions += float(amount)
	
	def fee(self, amount):
		"""Record the payment of a fee"""
		self.cash -= float(amount)
	
	def interest(self, amount):
		"""Record receipt of interest on cash balance"""
		self.cash += float(amount)
	
	def get_unit_value(self, date):
		"""Return the current value of one unit of the account"""
		if self.units == 0:
			return 1.
		else:
			return self.get_value(date) / self.units
	
	
	def get_value(self, date):
		"""Get the current value of the account"""
		value = self.cash
		#print self.portfolio
		for i in self.portfolio.itervalues():
			#print i
			if i['num'] > 0.:
				value += (i['num'] * float(i['obj'].get_price(date)))
		return value





def run():
	"""Run through all account transactions"""
	account = Account()
	c = csv.DictReader(open('account-transactions.csv', 'r'))
	lastdate = None
	oneday = timedelta(days=1)
	unitvalue = []
	contributions = []
	acvalue = []
	summary = {}
	for i in c:
		#print 'i: ', i
		date = datetime.strptime(i['Date'], '%d/%m/%Y')

		if (lastdate != None) and (date != (lastdate + oneday)):
			for x in range(1, (date - lastdate).days, 1):
				#Print summary for each date between lastdate and date
				# print 'summary: ', lastdate + oneday * x, \
				# 		account.get_value(lastdate + oneday * x), \
				# 		account.get_unit_value(lastdate + oneday * x)
				# unitvalue.append(account.get_unit_value(lastdate + oneday * x))
				# contributions.append(account.contributions)
				# acvalue.append(account.get_value(lastdate + oneday * x))
				summary[lastdate + oneday * x] = {'unit':account.get_unit_value(lastdate + oneday * x), \
													'contrib':account.contributions, \
													'acvalue':account.get_value(lastdate + oneday * x)}
		
		if i['Action'] == 'RECEIPT':
			account.add_money(i['Value'], date)
		elif i['Action'] == 'BUY':
			account.buy(i['Ticker'], i['Number'], i['Price'], i['Charges'], date)
		elif i['Action'] == 'SELL':
			account.sell(i['Ticker'], i['Number'], i['Price'], i['Charges'])
		elif i['Action'] == 'DIVIDEND':
			account.dividend(i['Ticker'], i['Value'])
		elif i['Action'] == 'FEE':
			account.fee(i['Charges'])
		elif i['Action'] == 'INTEREST':
			account.interest(i['Value'])
		lastdate = date
		
		#print 'summary: ', date, account.get_value(date), account.get_unit_value(date)
		#unitvalue.append(account.get_unit_value(date))
		#contributions.append(account.contributions)
		#acvalue.append(account.get_value(date))
		summary[date] = {'unit':account.get_unit_value(date), \
						'contrib':account.contributions, \
						'acvalue':account.get_value(date)}
	
	dates = summary.keys()
	dates.sort()
	
	unitvalues = []
	contribution = []
	acvalue = []
	for date in dates:
		unitvalues.append(summary[date]['unit'])
		contributions.append(summary[date]['contrib'])
		acvalue.append(summary[date]['acvalue'])

	print len(dates), len(unitvalues), len(contributions), len(acvalue)
	#Display charts
	fig = plt.figure()
	ax1 = fig.add_subplot(221)
	ax1.plot(dates, unitvalues, 'k-')
	ax1.set_title('Unit value')
	fig.autofmt_xdate()

	ax2 = fig.add_subplot(222)
	ax2.plot(dates, acvalue, 'k-')
	ax2.plot(dates, contributions, 'b-')
	ax2.set_title('Total value and contributions')
	fig.autofmt_xdate()

	ax3 = fig.add_subplot(223)
	ax3.plot(dates, np.array(acvalue) - np.array(contributions), 'k-')
	ax3.set_title('Value - contributions')

	fig.autofmt_xdate()
	plt.show()

	#Calculate annual rate of return
	
	annual_return(summary, datetime(day=3, month=8, year=2006))
	print '\n'
	annual_return(summary, datetime(day=5, month=1, year=2007))
	print '\n'
	annual_return(summary, datetime(day=1, month=4, year=2007))
	
		
	return summary

def annual_return(summary, startdate):
	oneyear = timedelta(days=365)
	enddate = startdate + oneyear
	print 'Start date: ', startdate.strftime('%Y-%m-%d')
	while enddate < datetime.now():
		pcreturn = 100 * (summary[enddate]['unit'] - summary[startdate]['unit']) / summary[startdate]['unit']
		print '%d/%d: %f' % (startdate.year, enddate.year, pcreturn)
		startdate = enddate
		enddate += oneyear