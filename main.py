import streamlit, sys

## Global Variable
ARG_Count: int = len(sys.argv)
ARG_Flags: int = 0
# Flag 0 = Mode selected
# Flag 1 = help mode
# Flag 2 = tui (Use to run without streamlit / Display to terminal)

## Argument Handling
if (ARG_Count > 1) :
    for i in sys.argv[1:] :
        if not (ARG_Flags & 1):
            if (i == "--help"):
                ARG_Flags |= (1 << 1)
            elif (i == "--tui"):
                ARG_Flags |= (1 << 2)
            ARG_Flags |= 1 


def main():
    streamlit.text("Hello from swe-team-beta!") # Static text
    print("Hello from swe-team-beta!")


if __name__ == "__main__":
    main()
