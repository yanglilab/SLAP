class AlzheimerRecord(object):
    def __init__(self, filename, diagnosis_id, image_id, colport, status, age, gender, mmse, apoe, site, race, tesla, sequence, scanner, scan_date):
        self.filename = filename
        self.diagnosis_id = diagnosis_id
        self.image_id = image_id
        self.colport = colport
        self.status = status
        self.age = age
        self.gender = gender
        self.mmse = mmse
        self.apoe = apoe
        self.site = site
        self.race = race
        self.tesla = tesla
        self.sequence = sequence
        self.scanner = scanner
        self.scan_date = scan_date

    def to_dict(self):
        return {
            'filename': self.filename,
            'diagnosis_id': self.diagnosis_id,
            'image_id': self.image_id,
            'colport': self.colport,
            'status': self.status,
            'age': self.age,
            'gender': self.gender,
            'mmse': self.mmse,
            'apoe': self.apoe,
            'site': self.site,
            'race': self.race,
            'tesla': self.tesla,
            'sequence': self.sequence,
            'scanner': self.scanner,
            'scan_date': self.scan_date
        }