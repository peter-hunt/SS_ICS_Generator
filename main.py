from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from random import randint

from flask import *
from pdfminer.high_level import extract_text

# lightsail push command:
# aws lightsail push-container-image --service-name flask-service
#     --label flask-container --image flask --region ca-central-1


period_map = [
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
start_time_map = [
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
end_time_map = [
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


@dataclass
class Course:
    name: str
    block: str
    is_lab: bool
    is_late: bool


@dataclass
class StudentSchedule:
    student_id: str
    A: Course
    B: Course
    C: Course
    D: Course
    E: Course
    F: Course
    G: Course
    H: Course

    def courseObj(self, label):
        if label not in {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'}:
            raise ValueError(f'invalid label: {label!r}')
        else:
            return getattr(self, label)


def get_starttime(index, late, wed):
    return start_time_map[int(wed)][index - 1][int(late)]


def get_endtime(index, late, wed, is_lab):
    if index in {1, 4} and is_lab:
        return end_time_map[int(wed)][index][int(late)]
    else:
        return end_time_map[int(wed)][index - 1][int(late)]


def period(day, period_):
    return period_map[day][period_]


def random_UID():
    a = randint(0, 100000)
    b = hex(randint(0, 65535))[2:]
    c = hex(randint(0, 65535))[2:]
    d = hex(randint(0, 65535))[2:]
    return f'4F2F7F11-{d}-{c}-{b}-6634746{a}'


def new_event(name: str, start_time, end_time, location, time: datetime, file):
    """
        OK this function is kinda poop, it would be better if startTime and
    endTime parameter can be passed through as dateTime object.

    This would require some changes in the start_time_map and end_time_map arrays.
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
    global student_schedule
    global student_id
    global prev_student_id
    if request.method == 'POST':
        student_id = request.form['studentID']
        student_schedule = StudentSchedule(
            student_id,
            Course(request.form['blockA'], 'A',
                   is_checked(request.form.get('blockAlab', False)),
                   is_checked(request.form.get('blockAlate', False))),
            Course(request.form['blockB'], 'B',
                   is_checked(request.form.get('blockBlab', False)),
                   is_checked(request.form.get('blockBlate', False))),
            Course(request.form['blockC'], 'C',
                   is_checked(request.form.get('blockClab', False)),
                   is_checked(request.form.get('blockClate', False))),
            Course(request.form['blockD'], 'D',
                   is_checked(request.form.get('blockDlab', False)),
                   is_checked(request.form.get('blockDlate', False))),
            Course(request.form['blockE'], 'E',
                   is_checked(request.form.get('blockElab', False)),
                   is_checked(request.form.get('blockElate', False))),
            Course(request.form['blockF'], 'F',
                   is_checked(request.form.get('blockFlab', False)),
                   is_checked(request.form.get('blockFlate', False))),
            Course(request.form['blockG'], 'G',
                   is_checked(request.form.get('blockGlab', False)),
                   is_checked(request.form.get('blockGlate', False))),
            Course(request.form['blockH'], 'H',
                   is_checked(request.form.get('blockHlab', False)),
                   is_checked(request.form.get('blockHlate', False))),
        )

        cycle_day_map = []
        with open('blockSchedule.txt') as file:
            current_time = datetime.now()
            for lineTxt in file.read().strip().split('\n'):
                txt = lineTxt.split('+')
                time_obj = datetime.strptime(txt[0], '%A,%b%d').replace(
                    year=current_time.year)
                data = [time_obj, txt[1]]
                cycle_day_map.append(data)

        dates = []
        course_names = []
        start_times = []
        end_times = []

        for day in cycle_day_map:
            periods = period_map[int(day[1]) - 1]
            period_num = 1
            isWed = date(day[0].year, day).weekday() == 2
            for i in periods:
                if student_schedule.courseObj(i).name != '':
                    dates.append(day[0])
                    course_names.append(student_schedule.courseObj(i).name)
                    start_times.append(get_starttime(
                        period_num, student_schedule.courseObj(i).is_late, isWed))
                    end_times.append(
                        get_endtime(
                            period_num, student_schedule.courseObj(i).is_late,
                            isWed, student_schedule.courseObj(i).is_lab))
                    print(f'{day[0]}={student_schedule.courseObj(i).name}'
                          f'={period_num}\n')
                period_num += 1

        with open(f'{student_schedule.student_id}_schedule.ics', 'w') as file:
            file.write(headings_str)
            for i in range(len(dates)):
                new_event(course_names[i], start_times[i], end_times[i],
                          'School', dates[i], file)
            file.write('END:VCALENDAR')

    if Path(f'{prev_student_id}.ics').is_file():
        Path(f'{prev_student_id}.ics').unlink()

    prev_student_id = student_id

    return redirect('/file_download', 302)


@app.route('/file_download')
def file_downloads():
    try:
        return render_template('downloads.html')
    except Exception as e:
        return f'{e}'


@app.route('/return-files/')
def sendFile():
    try:
        return send_file(f'{student_id}_schedule.ics')
    except Exception as e:
        return f'{e}'


@app.route('/adv-filler-page/')
def adv_filler():
    return render_template('adv-schedule-filler.html')


@app.route('/send-adv-schedule/', methods=['POST', 'GET'])
def send_adv_schedule():
    # Backend not completed!!!!
    adv_schedule_list = [[''] * 6 for _ in range(8)]

    for day in range(8):
        for prd in range(6):
            input_id = f'day-{day + 1}-period-{prd + 1}-in'
            adv_schedule_list[day][prd] = request.form[input_id]
    student_id_adv = request.form['stu-id-in']
    # Input processing wrote into 2D lst
    cycleDays = []
    with open('blockSchedule.txt') as file:
        current_time = datetime.now()
        for line in file.strip().split('\n'):
            txt = line.split('+')
            time_obj = datetime.strptime(txt[0], '%A,%b%d').replace(
                year=current_time.year)
            data = [time_obj, int(txt[1])]
            cycleDays.append(data)
            print(data)
    # Pulled cycle day schedule from file
    with open(f'{student_id_adv}_schedule.ics', 'w') as file:
        file.write(headings_str)
        for day in cycleDays:
            for p in range(6):
                print(day[1])
                if adv_schedule_list[day[1] - 1][p] != '':
                    isWed = date(day[0].year, day).weekday() == 2
                    new_event(adv_schedule_list[day[1] - 1][p],
                              get_starttime(p + 1, False, isWed),
                              get_endtime(p + 1, True, isWed, False),
                              'School', day[0], file)
        file.write('END:VCALENDAR')

    try:
        fileName = f'{student_id_adv}_schedule.ics'
        return send_file(fileName)
    except Exception as e:
        return f'{e}'


@app.route('/ocr-filler/')
def ocr_filler():
    return render_template('ocr-filler.html')


@app.route('/ocr-download/')
def download_ocr_file():
    try:
        return send_file('Your Schedule.ics')
    except Exception as e:
        return f'{e}'


@app.route('/send-ocr-schedule/', methods=['POST', 'GET'])
def send_ocr_schedule():
    global prev_student_id
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
        cycle_day_map = []
        with open('blockSchedule.txt', 'r') as file:
            current_time = datetime.now()
            for line in file.read().strip().split('\n'):
                txt = line.split('+')
                time_obj = datetime.strptime(txt[0], '%A,%b%d').replace(
                    year=current_time.year)
                data = [time_obj, txt[1]]
                cycle_day_map.append(data)

        print(cycle_day_map)

        with open('Your Schedule.ics', 'w') as file:
            file.write(headings_str)

            for day in cycle_day_map:
                periods = period_map[int(day[1]) - 1]
                period_num = 1
                isWed = date(day[0].year, day).weekday() == 2
                for i in periods:
                    j = 'ABCDEFGH'.index(i)
                    if blocksList[j] != '':
                        new_event(
                            blocksList[j],
                            get_starttime(period_num, lateList[j], isWed),
                            get_endtime(period_num, lateList[j], isWed, 0),
                            locationList[j], day[0], file)
                    period_num += 1

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
