# Test the ARR2019 dialog fix in QGIS

The fix keeps the existing ARR2019 extraction dialog open after both errors
and successful runs. Dismiss the result popup, change settings if needed,
and select **Run** again. Select **Close** when finished.

## Build an installable test ZIP

In PowerShell, clone the test branch and run the build script:

```powershell
git clone --branch fix/arr2019-keep-dialog-open https://github.com/Chain-Frost/QGIS-TUFLOW-Plugin.git
Set-Location QGIS-TUFLOW-Plugin
python scripts/build_arr2019_test_plugin.py
```

The build script uses Python's standard library. QGIS does not need to be
running to build the archive. The output is:

```text
dist/tuflow-2026.1.7-arr-dialog-test.zip
```

The script starts with the complete official TUFLOW **2026.1.7** plugin
archive and replaces these three files with the versions in this checkout:

- `tuflow/tuflowqgis_dialog.py`
- `tuflow/forms/ui_tuflowqgis_arr2016.py`
- `tuflow/forms/ui_tuflowqgis_arr2016.ui`

It verifies the base release and original source hashes before replacing
files. All other packaged files, including bundled dependencies and license
files, are preserved. The archive has one top-level `tuflow` directory.
The generated Python UI is already updated, so no UI compilation is needed.

If the automatic download is blocked, download the official ZIP in your
browser from the [2026.1.7 release page](https://plugins.qgis.org/plugins/tuflow/version/2026.1.7/),
save it as `build/tuflow-2026.1.7-official.zip` beneath this checkout, and run
the script again. Create the `build` directory if necessary. A validation
failure should be investigated; do not substitute an arbitrary plugin version.

This packaging method avoids needing local submodule checkouts. The source
repository has four submodules, including `tuflow/pt`, which is required when
the plugin loads. A GitHub **Download ZIP** or a ZIP of an incomplete checkout
does not include their contents. The official plugin archive already includes
the packaged runtime dependencies.

The source metadata stays at version **2026.1.7**. Identify this test build by
its archive filename and by the **Run / Close** buttons in the ARR2019 dialog.

## Install in QGIS

1. Select **Settings > User Profiles > New profile...** and name it
   `ARR2019-test`. QGIS opens a new instance with that profile.
2. In that instance, select **Plugins > Manage and Install Plugins... >
   Install from ZIP**.
3. Select `dist/tuflow-2026.1.7-arr-dialog-test.zip` and install it.
4. Enable **TUFLOW** if necessary. If you replaced a copy already loaded in
   this test profile, restart that QGIS instance to load the changed Python.
5. Open your project or catchment layer and the **Extract ARR2019 to TUFLOW**
   tool. Confirm the buttons read **Run** and **Close**.

QGIS profiles keep their settings and installed plugins separately. This
package uses the existing plugin identifier `tuflow`; installing it in an
existing profile replaces that profile's TUFLOW plugin. Return to your normal
profile through **Settings > User Profiles** after testing.

Official references:

- [QGIS: Install from ZIP](https://docs.qgis.org/3.44/en/docs/user_manual/plugins/plugins.html#the-install-from-zip-tab)
- [QGIS: Working with User Profiles](https://docs.qgis.org/3.44/en/docs/user_manual/introduction/qgis_configuration.html#working-with-user-profiles)

## Local acceptance checks

Use a separate output folder for the test runs. Record your QGIS version and
the branch commit tested.

| Check | Expected result |
| --- | --- |
| The processing error that previously closed the dialog | The error popup still appears. Dismissing it leaves the form open, every input retained, a normal cursor, and Run/Close enabled. |
| Correct the inputs and run again | The next run starts in the same dialog and uses the current settings. |
| Successful completion | The success popup still appears. Dismissing it leaves the form open and ready for another run. |
| Change catchment, AEPs/durations or output folder and run again | The new selections are used. An error identifies the current catchment. |
| Several catchments and a quick failure | Progress updates correctly and there is one completion popup per batch, with no timer exception or lingering busy cursor. |
| Close after completion | Close and the window's close button dismiss the dialog. |

Keeping the current dialog open preserves its live settings. This change
does not add full settings persistence after deliberately closing the window
or restarting QGIS, and it does not change rainfall calculations.

## Verification already completed

The dialog patch passed eight isolated regression checks against its actual
Python methods using Qt substitutes, plus syntax, UI XML and whitespace
checks. The unmodified source reproduced seven failures and one passing
control. Native Qt event delivery, plugin activation and rainfall processing
still need the local QGIS checks above.
