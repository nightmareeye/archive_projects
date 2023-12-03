#include <windows.h>

#include <string>

#define EXIT_TIMER 1

LRESULT CALLBACK WindowProcedure(HWND, UINT, WPARAM, LPARAM);

LPCWSTR szClassName = L"WinLocker";

int counter = 10;

int WINAPI WinMain(HINSTANCE hInstance,
	HINSTANCE hPrevInstance,
	LPSTR lpszArgument,
	int nCmdShow)
{
	HWND hwnd;
	MSG messages;
	WNDCLASSEX wincl;

	wincl.hInstance = hInstance;
	wincl.lpszClassName = szClassName;
	wincl.lpfnWndProc = WindowProcedure;
	wincl.style = CS_DBLCLKS;
	wincl.cbSize = sizeof(WNDCLASSEX);

	wincl.hIcon = LoadIcon(NULL, IDI_APPLICATION);
	wincl.hIconSm = LoadIcon(NULL, IDI_APPLICATION);
	wincl.hCursor = LoadCursor(NULL, IDC_ARROW);
	wincl.lpszMenuName = NULL;
	wincl.cbClsExtra = 0;
	wincl.cbWndExtra = 0;
	wincl.hbrBackground = (HBRUSH)COLOR_BACKGROUND;

	if (!RegisterClassEx(&wincl))
		return 0;

	hwnd = CreateWindowEx(
		0,
		szClassName,
		L"Win Locker",
		WS_OVERLAPPED | WS_CAPTION | WS_THICKFRAME,
		CW_USEDEFAULT,
		CW_USEDEFAULT,
		200,
		150,
		HWND_DESKTOP,
		NULL,
		hInstance,
		NULL
	);

	ShowWindow(hwnd, nCmdShow);
	while (GetMessage(&messages, NULL, 0, 0))
	{
		TranslateMessage(&messages);
		DispatchMessage(&messages);
	}
	return messages.wParam;
}
HWND FreeCounterText;
LRESULT CALLBACK WindowProcedure(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam)
{
	switch (message)
	{
	case WM_CREATE:
		FreeCounterText = CreateWindow(L"STATIC", L"", WS_VISIBLE | WS_CHILD,
			10, 10, 24, 18, hwnd, NULL, NULL, NULL);
		SetTimer(hwnd, EXIT_TIMER, 1000, (TIMERPROC)NULL);
		//---------------
		BlockInput(true);
		//---------------
		break;
	case WM_TIMER:
		switch (wParam)
		{
		case EXIT_TIMER:
			counter--;
			SetWindowTextA(FreeCounterText, std::to_string(counter).c_str());
			if (counter < 1)
			{
				//----------------
				BlockInput(false);
				//----------------
				KillTimer(hwnd, EXIT_TIMER);
			}
			break;
		}
		break;
	case WM_DESTROY:
		KillTimer(hwnd, EXIT_TIMER);
		PostQuitMessage(0);
		break;
	default:
		return DefWindowProc(hwnd, message, wParam, lParam);
	}

	return 0;
}