import asyncio
from pathlib import Path
from constants import BASE_DIR, LINKS_FILE, USE_GUI
from hd_parse import parse_links_to_files, read_links
from loguru import logger


def init_logger() -> None:
    logger.add(
        sink=(BASE_DIR / 'log' / Path(__file__).stem).with_suffix('.log'),
        format='{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}',
        level='INFO',
        rotation='1 month',
        retention='2 months',
    )


def run_gui():
    import interface
    from PyQt5 import QtWidgets

    def gui_log(msg):
        window.logEdit.setText(window.logEdit.toPlainText() + '\n' + msg)
        window.logEdit.repaint()

    logger.add(sink=gui_log, format='{time:HH:mm:ss} | {level} | {message}', level='DEBUG')

    class HDApp(QtWidgets.QMainWindow, interface.Ui_MainWindow):
        def __init__(self):
            super().__init__()
            self.setupUi(self)
            self.pushButton.pressed.connect(self.pass_to_scrape)

        def pass_to_scrape(self):
            links = [link for link in self.textEdit.toPlainText().split('\n') if len(link) > 5]
            asyncio.run(parse_links_to_files(links))

    app = QtWidgets.QApplication([])
    window = HDApp()
    window.show()
    app.exec()


if __name__ == '__main__':
    try:
        init_logger()
        run_gui() if USE_GUI else asyncio.run(parse_links_to_files(read_links(LINKS_FILE)))
    except:
        logger.exception(f'Upper level Exception in {__file__}')
    finally:
        logger.complete()
