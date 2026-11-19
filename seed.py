"""Reset the database and load mock courses.

Usage: python seed.py   (wipes all enrollments)

The data is MOCK: TMU-style 3rd-year Computer Engineering courses. Codes and titles
are approximate and descriptions are made up.
"""

from app import create_app
from db import get_db, init_db

COURSES = [
    ("COE 528", "Object Oriented Eng Analysis and Design", "UML, design patterns and object-oriented design of software systems.", 1.0),
    ("COE 538", "Microprocessor Systems", "Assembly programming, interfacing and interrupts on embedded microcontrollers.", 1.0),
    ("COE 608", "Computer Organization and Architecture", "Datapaths, pipelining, memory hierarchy and instruction set design.", 1.0),
    ("COE 628", "Operating Systems", "Processes, threads, scheduling, synchronization, memory and file systems.", 1.0),
    ("COE 691", "Software Requirements Analysis and Spec", "Eliciting, modelling and validating software requirements.", 1.0),
    ("COE 692", "Software Design and Architecture", "Architectural styles, components and quality attributes of large systems.", 1.0),
    ("ELE 404", "Electronic Circuits I", "Diodes, transistors and amplifier circuits.", 1.0),
    ("ELE 532", "Signals and Systems I", "Continuous-time signals, convolution, Fourier series and transforms.", 1.0),
    ("ELE 635", "Communication Systems", "Analog and digital modulation, noise and channel capacity.", 1.0),
    ("ELE 639", "Control Systems", "Feedback, transfer functions, stability and root locus design.", 1.0),
    ("MTH 514", "Probability and Stochastic Processes", "Random variables, distributions and random processes for engineers.", 1.0),
    ("ECN 801", "Principles of Engineering Economics", "Time value of money, cost analysis and project evaluation.", 1.0),
]


def seed_db(db):
    db.executemany(
        "INSERT INTO courses (code, title, description, credits) VALUES (?, ?, ?, ?)",
        COURSES,
    )
    db.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        init_db()
        seed_db(get_db())
        print(f"Seeded {len(COURSES)} courses into {app.config['DATABASE']}")
