import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

root = Path('sermons')
if not root.exists():
    root.mkdir()

series_ls = [
#     'John',
#     'Romans',
#     'Proverbs',
# #     # # '1 Corinthians',
# #     # # '1 Peter',
# #     # # '1 Samuel',
# #     # # '1 Thessalonians',
# #     # '1 Timothy',
# #     # '2 Peter',
# #     # '2 Thessalonians',
# #     # '2 Timothy',
#     'Acts',
#     'Colossians',
# #     # # 'Daniel',
# #     # 'Ecclesiastes',
# #     # 'Ephesians',
# #     # 'Evangelism 101',
#     'Hebrews',
# #     # 'James',
# #     # 'Jeremiah',
#     'Job',
# #     # # 'Jonah',
# #     # 'Jude',
# #     # 'Luke',
# #     # 'Malachi',
# #     # 'Mark',
# #     # # 'Marriage and Family',
# #     # 'Matthew',
# #     # 'Nehemiah',
# #     # 'Pentateuch',
# #     # 'Philemon',
# #     # 'Philippians',
# #     # 'Proclaiming the Gospel',
#     'Psalms',
# #     # 'Ruth',
# #     # 'The Holy Spirit',
#     'The Sermon on the mount',
# #     # 'What is God like',
]

with open('element.txt') as element:
    main_page = BeautifulSoup(element, 'html.parser')
    for series in main_page.find_all('a', href=re.compile(r'.*series=.*')):
        series_url = series['ng-href']
        series_title = series_url[series_url.rfind('=')+1:]

        duds = []

        if series_title in series_ls:
            series_path = root / series_title

            if not series_path.exists():
                series_path.mkdir()

            series_data = requests.get(f'https://sermon-jay.herokuapp.com/resource-query?series={series_title}')
            series_page = BeautifulSoup(series_data.content, 'html.parser')

            sermons = []

            sermons_rows = series_page.find('table').find_all('tr')[1:][::-1]
            for sermon_row in sermons_rows:
                sermon_info = sermon_row.find_all('td')

                sermon_title = sermon_info[0].string
                sermon_preacher = sermon_info[1].string
                sermon_wotc = sermon_info[3].string
                sermon_date = sermon_info[4].string
                sermon_ref = sermon_info[5].string
                sermon_url = sermon_info[7].find('a', title='Download')['href']

                sermons.append(dict(
                    title=sermon_title,
                    preacher=sermon_preacher,
                    wotc=sermon_wotc,
                    date=sermon_date,
                    ref=sermon_ref,
                    url=sermon_url,
                ))

            sermons_df = pd.DataFrame(sermons)

            for i, r in sermons_df.iterrows():
                r.date = pd.to_datetime(r.date)

            sermons_df.title = sermons_df.title.str.replace(':', '_')
            sermons_df.title = sermons_df.title.str.replace('  ', ' ')
            sermons_df.title = sermons_df.title.str.replace('"', '')
            sermons_df.title = sermons_df.title.str.replace('“', '')
            sermons_df.title = sermons_df.title.str.replace('”', '')
            sermons_df.title = sermons_df.title.str.replace('?', '')
            sermons_df.title = sermons_df.title.str.replace('/', '-')
            sermons_df.title = sermons_df.title.str.replace('\\', '-')
            sermons_df.sort_values('date', inplace=True)
            sermons_df["fname"] = sermons_df.apply('{date:%Y-%m-%d} {title} ({ref}).mp3'.format_map, axis=1)
            sermons_df.fname = sermons_df.fname.str.replace(':', '_')
            sermons_df.fname = sermons_df.fname.str.replace('  ', ' ')
            sermons_df.fname = sermons_df.fname.str.replace('"', '')
            sermons_df.fname = sermons_df.fname.str.replace('“', '')
            sermons_df.fname = sermons_df.fname.str.replace('”', '')
            sermons_df.fname = sermons_df.fname.str.replace('?', '')
            sermons_df.fname = sermons_df.fname.str.replace('/', '-')
            sermons_df.fname = sermons_df.fname.str.replace('\\', '-')

            for i, sermon in sermons_df.iterrows():
                sermon_path = series_path / sermon.fname
                if not sermon_path.exists():
                    print(f'Downloading {sermon.fname}...', end=' ')
                    sermon_get = requests.get(sermon.url)
                    if sermon_get.status_code != 404:
                        with open(sermon_path, 'wb') as ff:
                                ff.write(sermon_get.content)

                                # mp3 = MP3File(str(sermon_path))
                                # mp3.set_version(VERSION_2)
                                # print()
                                # mp3.artist = sermon.preacher
                                # print(f'{sermon.preacher = !r}')
                                # print(f'{mp3.artist = !r}')
                                # mp3.album = series_title
                                # print(f'{series_title = !r}')
                                # mp3.save()
                                # print(f'{mp3.album = !r}')
                                # exit()
                                # mp3.song = sermon.title
                                # print(f'{sermon.title = !r}')
                                # print(f'{mp3.song = !r}')
                                # mp3.track = str(int(i) + 1)
                                # print(f'{int(i) + 1 = !r}')
                                # print(f'{mp3.track = !r}')
                                # del mp3.genre
                                # del mp3.comment
                                # mp3.save()

                                mp3 = MP3(sermon_path, ID3=EasyID3)
                                mp3["artist"] = sermon.preacher
                                mp3["album"] = series_title
                                mp3["title"] = f"{sermon.title} ({sermon.ref})"
                                mp3["tracknumber"] = str(int(i) + 1)
                                mp3["date"] = f"{sermon.date:%Y}"
                                mp3["originaldate"] = f"{sermon.date:%Y}"
                                mp3["albumartist"] = ""
                                mp3["genre"] = "Sermon"
                                mp3.save()

                                print('Done!')
                    else:
                        duds.append(sermon.fname)


            with open('duds.txt', 'w+') as ff:
                ff.writelines(duds)

with open('series.txt', 'w') as ff:
    ff.write(',\n'.join(series_ls))
