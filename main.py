from datetime import datetime
from pathlib import Path
from random import randint

from flask import *
from pdfminer.high_level import extract_text

# lightsail push command:
# aws lightsail push-container-image --service-name flask-service
#     --label flask-container --image flask --region ca-central-1


periodMap = [
    ['A', 'B', 'C', 'D', 'E', 'F'],
    ['G', 'D', 'E', 'H', 'A', 'B'],
    ['F', 'H', 'A', 'C', 'G', 'D'],
    ['B', 'C', 'G', 'E', 'F', 'H'],
    ['D', 'E', 'F', 'A', 'B', 'C'],
    ['H', 'A', 'B', 'G', 'D', 'E'],
    ['C', 'G', 'D', 'F', 'H', 'A'],
    ['E', 'F', 'H', 'B', 'C', 'G'],
]

# for these two maps, index 0 is for regular day and index 1 is for wednesdays
startTimeMap = [
    [
        # Normal Day schedule
        ['081500', '081500'],
        ['091000', '091000'],
        ['103500', '103500'],
        ['115000', '122500'],
        ['132000', '132000'],
        ['141500', '141500'],
    ],
    [
        # Wednesday schedule
        ['093500', '093500'],
        ['103000', '103000'],
        ['112500', '112500'],
        ['122000', '124500'],
        ['134000', '134000'],
        ['143500', '143500'],
    ]
]
endTimeMap = [
    [
        # Normal schedule
        ['090500', '090500'],
        ['100500', '100500'],
        ['114500', '114500'],
        ['124000', '131500'],
        ['141000', '141000'],
        ['150000', '150000'],
    ],
    [
        # Wednesday schedule
        ['102500', '102500'],
        ['112000', '112000'],
        ['121500', '121500'],
        ['131000', '133500'],
        ['143000', '143000'],
        ['152500', '152500'],
    ]
]


class Course:
    def __init__(self, name, block, lab, late):
        self.name = name
        self.block = block
        self.lab = lab
        self.late = late


class StudentSchedule:
    def __init__(self, student_id, A, B, C, D, E, F, G, H):
        self.student_id = student_id
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self.E = E
        self.F = F
        self.G = G
        self.H = H

    def courseObj(self, label):
        if label not in {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'}:
            raise ValueError(f'invalid label: {label!r}')
        else:
            return getattr(self, label)


def get_starttime(index, late, wed):
    return startTimeMap[int(wed)][index - 1][int(late)]


def get_endtime(index, late, wed, is_lab):
    if index in {1, 4} and is_lab:
        return endTimeMap[int(wed)][index][int(late)]
    else:
        return endTimeMap[int(wed)][index - 1][int(late)]


def period(day, period_):
    return periodMap[day][period_]


def random_UID():
    a = randint(0, 100000)
    b = hex(randint(0, 65535))[2:]
    c = hex(randint(0, 65535))[2:]
    d = hex(randint(0, 65535))[2:]
    return f'4F2F7F11-{d}-{c}-{b}-6634746{a}'


def new_event(name, start_time, end_time, location, time, file):
    """
        OK this function is kinda poop, it would be better if startTime and
    endTime parameter can be passed through as dateTime object.

    This would require some changes in the startTimeMap and endTimeMap arrays.
    It would also need the complete restructure of the algorithm.
    """

    year = time.strftime('%Y')
    month = time.strftime('%m')
    day = time.strftime('%d')
    hour = time.strftime('%H')
    minute = time.strftime('%M')
    second = time.strftime('%S')

    file.write(
        f'BEGIN:VEVENT\n'
        f'TRANSP:OPAQUE\n'
        f'DTEND;TZID=America/New_York:{year}{month}{day}T{end_time}\n'
        f'UID:{random_UID()}\n'
        f'DTSTAMP:20210903T163112Z\n'
        f'LOCATION:{location}\n'
        f'URL;VALUE=URI:\n'
        f'SEQUENCE:0\n'
        f'X-APPLE-TRAVEL-ADVISORY-BEHAVIOR:AUTOMATIC\n'
        f'SUMMARY:{name}\n'
        f'LAST-MODIFIED:{year}{month}{day}T{hour}{minute}{second}Z\n'
        f'CREATED:{year}{month}{day}T{hour}{minute}{second}Z\n'
        f'DTSTART;TZID=America/New_York:{year}{month}{day}T{start_time}\n'
        f'BEGIN:VALARM\n'
        f'X-WR-ALARMUID:{random_UID()}\n'
        f'UID:{random_UID()}\n'
        f'DESCRIPTION:Reminder\n'
        f'ACKNOWLEDGED:20210903T163112Z\n'
        f'TRIGGER:-PT5M\n'
        f'ACTION:DISPLAY\n'
        f'END:VALARM\n'
        f'END:VEVENT\n'
    )


def is_checked(string):
    return string == 'True'


headings_str = (
    'BEGIN:VCALENDAR\n'
    'METHOD:PUBLISH\n'
    'VERSION:2.0\n'
    'X-WR-CALNAME:SSA Calendar\n'
    'PRODID:-//Apple Inc.//macOS 11.5.2//EN\n'
    'X-APPLE-CALENDAR-COLOR:#34AADC\n'
    'X-WR-TIMEZONE:America/New_York\n'
    'CALSCALE:GREGORIAN\n'
    'BEGIN:VTIMEZONE\n'
    'TZID:America/New_York\n'
    'BEGIN:DAYLIGHT\n'
    'TZOFFSETFROM:-0500\n'
    'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU\n'
    'DTSTART:20070311T020000\n'
    'TZNAME:EDT\n'
    'TZOFFSETTO:-0400\n'
    'END:DAYLIGHT\n'
    'BEGIN:STANDARD\n'
    'TZOFFSETFROM:-0400\n'
    'RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU\n'
    'DTSTART:20071104T020000\n'
    'TZNAME:EST\n'
    'TZOFFSETTO:-0500\n'
    'END:STANDARD\n'
    'END:VTIMEZONE\n'
)


app = Flask(__name__)


@app.route('/schedule-filler/')
def schedule_nav_page():
    return render_template('schedule-filler.html')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/fill_schedule', methods=['POST', 'GET'])
def fillSchedulePage():
    global studentSchedule
    global studentID
    global prevStudentID
    if request.method == 'POST':
        studentID = request.form['studentID']
        blockA = Course(request.form['blockA'], 'A',
                        is_checked(request.form.get('blockAlab', False)),
                        is_checked(request.form.get('blockAlate', False)))
        blockB = Course(request.form['blockB'], 'B',
                        is_checked(request.form.get('blockBlab', False)),
                        is_checked(request.form.get('blockBlate', False)))
        blockC = Course(request.form['blockC'], 'C',
                        is_checked(request.form.get('blockClab', False)),
                        is_checked(request.form.get('blockClate', False)))
        blockD = Course(request.form['blockD'], 'D',
                        is_checked(request.form.get('blockDlab', False)),
                        is_checked(request.form.get('blockDlate', False)))
        blockE = Course(request.form['blockE'], 'E',
                        is_checked(request.form.get('blockElab', False)),
                        is_checked(request.form.get('blockElate', False)))
        blockF = Course(request.form['blockF'], 'F',
                        is_checked(request.form.get('blockFlab', False)),
                        is_checked(request.form.get('blockFlate', False)))
        blockG = Course(request.form['blockG'], 'G',
                        is_checked(request.form.get('blockGlab', False)),
                        is_checked(request.form.get('blockGlate', False)))
        blockH = Course(request.form['blockH'], 'H',
                        is_checked(request.form.get('blockHlab', False)),
                        is_checked(request.form.get('blockHlate', False)))
        studentSchedule = StudentSchedule(
            studentID, blockA, blockB, blockC, blockD,
            blockE, blockF, blockG, blockH,
        )

        cycleDayMap = []
        with open('blockSchedule.txt') as file:
            currentTime = datetime.now()
            for lineTxt in file.read().strip().split('\n'):
                txt = lineTxt.split('+')
                timeObj = datetime.strptime(txt[0], '%A,%b%d').replace(
                    year=currentTime.year)
                data = [timeObj, txt[1]]
                cycleDayMap.append(data)

        dateLst = []
        courseNameLst = []
        startTimeLst = []
        endTimeLst = []

        for day in cycleDayMap:
            periodLst = periodMap[int(day[1]) - 1]
            periodNum = 1
            isWed = int(day[0].strftime('%w') == '3')
            for i in periodLst:
                if studentSchedule.courseObj(i).name != '':
                    dateLst.append(day[0])
                    courseNameLst.append(studentSchedule.courseObj(i).name)
                    startTimeLst.append(get_starttime(
                        periodNum, studentSchedule.courseObj(i).late, isWed))
                    endTimeLst.append(
                        get_endtime(
                            periodNum, studentSchedule.courseObj(i).late,
                            isWed, studentSchedule.courseObj(i).lab))
                    print(f'{day[0]}={studentSchedule.courseObj(i).name}'
                          f'={periodNum}\n')
                periodNum += 1

        with open(f'{studentSchedule.student_id}_schedule.ics', 'w') as file:
            file.write(headings_str)
            for i in range(len(dateLst)):
                new_event(courseNameLst[i], startTimeLst[i], endTimeLst[i],
                          'School', dateLst[i], file)
            file.write('END:VCALENDAR')

    if Path(f'{prevStudentID}.ics').is_file():
        Path(f'{prevStudentID}.ics').unlink()

    prevStudentID = studentID

    return redirect('/file_download', 302)


@app.route('/file_download')
def file_downloads():
    try:
        return render_template('downloads.html')
    except Exception as e:
        return str(e)


@app.route('/return-files/')
def sendFile():
    try:
        return send_file(f'{studentID}_schedule.ics')
    except Exception as e:
        return str(e)


@app.route('/adv-filler-page/')
def adv_filler():
    return render_template('adv-schedule-filler.html')


@app.route('/send-adv-schedule/', methods=['POST', 'GET'])
def send_adv_schedule():
    # Not completed backend!!!!
    advScheduleLst = [[''] * 6 for i in range(8)]

    for day in range(8):
        for prd in range(6):
            inputId = f'day-{day+1}-period-{prd+1}-in'
            advScheduleLst[day][prd] = request.form[inputId]
    studentID_adv = request.form['stu-id-in']
    # Input processing wrote into 2D lst
    cycleDays = []
    with open('blockSchedule.txt') as file:
        currentTime = datetime.now()
        for line in file.strip().split('\n'):
            txt = line.split('+')
            timeObj = datetime.strptime(txt[0], '%A,%b%d').replace(
                year=currentTime.year)
            data = [timeObj, int(txt[1])]
            cycleDays.append(data)
            print(data)
    # Pulled cycle day schedule from file
    with open(studentID_adv+'_schedule.ics', 'w') as file:
        file.write(headings_str)

        for day in cycleDays:
            for p in range(6):
                print(day[1])
                if advScheduleLst[day[1]-1][p] != '':
                    isWed = day[0].strftime('%w') == '3'
                    new_event(advScheduleLst[day[1]-1][p],
                              get_starttime(p+1, False, isWed),
                              get_endtime(p+1, True, isWed, False),
                              'School', day[0], file)
        file.write('END:VCALENDAR')

    try:
        fileName = f'{studentID_adv}_schedule.ics'
        return send_file(fileName)
    except Exception as e:
        return str(e)


@app.route('/ocr-filler/')
def ocr_filler():
    return render_template('ocr-filler.html')


@app.route('/ocr-download/')
def download_ocr_file():
    try:
        return send_file('Your Schedule.ics')
    except Exception as e:
        return str(e)


@app.route('/send-ocr-schedule/', methods=['POST', 'GET'])
def send_ocr_schedule():
    global prevStudentID
    if request.method == 'POST':
        pdfFile = request.files['schedule-pdf']
        pdfFile.save('temp.pdf')
        extractedText = extract_text('temp.pdf')
        extractedBlocks = extractedText.split('\n\n')
        extractedBlocks = extractedBlocks[15:45]

        blocksList = [''] * 8  # order(0-7) ABCDEFGH
        locationList = [''] * 8
        lateList = [0] * 8

        for block in extractedBlocks:
            txt = block.replace('\n', ' ')
            print(txt)
            if (':' in txt and txt[0:11] != 'Unscheduled'
                    and txt[0:9] != 'Community'):
                periodInfoStr = txt[txt.index('(') + 8:txt.index(')')-1]
                current_period = 'ABCDEFGH'.index(periodInfoStr[0])
                rep = False
                for a in blocksList:
                    if a == txt[0:txt.index(':')]:
                        rep = True

                if not rep:
                    blocksList[current_period] = txt[0:txt.index(':')]
                    locationList[current_period] = block[
                        block.index(')') + 1:len(block)].replace('\n', ' ')
                    lateList[current_period] = int(periodInfoStr[-1] == 'L')

        print(blocksList)
        cycleDayMap = []
        with open('blockSchedule.txt', 'r') as file:
            currentTime = datetime.now()
            for line in file.read().strip().split('\n'):
                txt = line.split('+')
                timeObj = datetime.strptime(txt[0], '%A,%b%d').replace(
                    year=currentTime.year)
                data = [timeObj, txt[1]]
                cycleDayMap.append(data)

        print(cycleDayMap)

        with open('Your Schedule.ics', 'w') as file:
            file.write(headings_str)

            for day in cycleDayMap:
                periodLst = periodMap[int(day[1]) - 1]
                periodNum = 1
                isWed = int(day[0].strftime('%w') == '3')
                for i in periodLst:
                    j = 'ABCDEFGH'.index(i)
                    if blocksList[j] != '':
                        new_event(
                            blocksList[j],
                            get_starttime(periodNum, lateList[j], isWed),
                            get_endtime(periodNum, lateList[j], isWed, 0),
                            locationList[j], day[0], file)
                    periodNum += 1

            file.write('END:VCALENDAR')

        return redirect('/ocr-download/')


@app.route('/upload-cycle-days/')
def upload_cycle_days():
    return render_template('cycle-days-upload.html')


@app.route('/write-cycle-days/', methods=['POST', 'GET'])
def write_cycle_days():
    if request.method == 'POST':
        txtFile = request.files['cycle-days-txt']
        Path('blockSchedule.txt').unlink()
        txtFile.save('blockSchedule.txt')
    return redirect('/')


if __name__ == '__main__':
    app.run(port=2328, host='0.0.0.0', debug=True)
