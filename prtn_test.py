#!/usr/bin/env python3

"""
PRTN Test Tool for UCIe 2.5D/3D Test System

This tool provides a simple interface for running single PRTN readouts:
- Performs soft reset at the start
- Runs all 4 EW configurations (1, 2, 3, 4)
- For each EW, combines readouts from all 4 block_idx (0, 1, 2, 3)
- Outputs 4 combined readout strings

Usage:
    python prtn_test.py

Author: Generated for UCIe Test System
Date: 2025
"""

import sys
import os
import datetime
import logging
import time

# Import the actual system components
from Raspberry_Pico import Pico
from Instrument import D2D_Subprogram
from Glink_phy import UCIe_2p5D as Glink_phy
from Glink_run import UCIe_2p5D as Glink_run

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class PRTNTestSystem:
    """
    PRTN test system following the GUI initialization flow
    """

    def __init__(self):
        """Initialize the complete test system following GUI flow"""
        logger.info("=" * 80)
        logger.info("UCIe 2.5D/3D PRTN Test System")
        logger.info("=" * 80)
        logger.info(f"Start Time: {datetime.datetime.now()}")
        logger.info("")

        # Initialize system components in the correct order
        self._initialize_gui_mock()
        self._initialize_i2c_communication()
        self._initialize_jtag()
        self._initialize_instrument_control()
        self._initialize_physical_layer()
        self._initialize_test_controller()

        logger.info("System initialization completed successfully!")
        logger.info("")

    def _initialize_gui_mock(self):
        """Create GUI mock object with all required attributes from MainFrame"""
        logger.info("Step 1: Initializing GUI Mock Object...")

        class GUIMock:
            """Mock GUI object with all required attributes from MainFrame"""

            def __init__(self):
                # Core attributes from MainFrame.__init__
                self.rst_visa = "USB0::0x2A8D::0x3302::MY59001241::0::INSTR"
                self.EHOST = [
                    [0x01, 0x02, 0x03],  # Die0 tport/H/V
                    [0x01, 0x02, 0x03],  # Die1 tport/H/V
                    [0x01, 0x02, 0x03],  # Die2 tport/H/V
                ]
                self.eye_graph_en = 0
                self.test_str_org = ["Load"]
                self.pass_fail = "NA"
                self.Temp_now = "NA"
                self.i2c = None
                self.phy_0 = None
                self.Spec = None
                self.run_0 = None
                self.jtag = None
                self.GROUP = 4
                self.SLICE = 8
                self.vef_num = 64
                self.slice = [0, 1, 2, 3]
                self.Power_Select = ""
                self.TP_use = 0
                self.abp_en = 0
                self.ini_wo_reset = 1
                self.font = "Arial"
                self.tools_path = os.path.dirname(os.path.abspath(__file__))

                # Power supply VISA addresses
                self.E363xA_visa = type(
                    "obj",
                    (object,),
                    {"Value": "USB0::0x2A8D::0x3302::MY59001241::0::INSTR"},
                )()

                logger.info("   ✓ GUI mock object created with all required attributes")

            def E363xA_Out_ON(self, **kwargs):
                """Power supply enable"""
                logger.info("   ✓ Power supplies enabled")
                pass

            def E363xA_Out_OFF(self, **kwargs):
                """Power supply disable"""
                logger.info("   ✓ Power supplies disabled")
                pass

        self.gui = GUIMock()
        logger.info("   ✓ GUI mock initialization completed")

    def _initialize_i2c_communication(self):
        """Initialize I2C communication with Raspberry Pi Pico"""
        logger.info("Step 2: Initializing I2C Communication...")
        try:
            logger.info("   → Attempting to connect to Raspberry Pi Pico...")
            self.i2c = Pico("7-bit")
            if self.i2c.pyb is None:
                logger.warning("   ⚠ No Pico device found!")
                logger.warning("   ⚠ Please ensure Pico is connected via USB")
                raise Exception("Pico device not found")

            logger.info("   ✓ Pico I2C communication established")

            # Get I2C scan results properly
            try:
                scan_result = self.i2c.to_list(self.i2c.pyb.eval("i2c.scan()"))
                scan_hex = list(map(hex, scan_result))
                logger.info(f"   ✓ I2C devices found: {scan_hex}")
            except Exception as scan_e:
                logger.warning(f"   ⚠ I2C scan failed: {scan_e}")
                logger.info("   ✓ I2C communication established (scan failed)")

            logger.info(
                "   ℹ Note: This connection will be closed when physical layer initializes"
            )
        except Exception as e:
            logger.error(f"   ✗ I2C initialization failed: {e}")
            logger.error("   ✗ Cannot proceed without I2C communication")
            raise

    def _initialize_jtag(self):
        """Initialize JTAG (set to None as in GUI system)"""
        logger.info("Step 3: Initializing JTAG...")
        self.jtag = None  # JTAG not used in this system
        logger.info("   ✓ JTAG initialized (set to None)")
        logger.info("   ✓ JTAG not required for this system")

    def _initialize_instrument_control(self):
        """Initialize instrument control (VISA)"""
        logger.info("Step 4: Initializing Instrument Control...")
        try:
            self.visa = D2D_Subprogram(self.gui)
            logger.info("   ✓ Instrument control initialized")
            logger.info("   ✓ VISA communication ready")
        except Exception as e:
            logger.warning(f"   ⚠ Instrument control initialization warning: {e}")
            logger.warning("   ⚠ Continuing without instrument control")

    def _initialize_physical_layer(self):
        """Initialize physical layer (Glink_phy)"""
        logger.info("Step 5: Initializing Physical Layer...")
        try:
            # Close our I2C connection first to avoid conflicts
            if hasattr(self.i2c, "pyb") and self.i2c.pyb is not None:
                try:
                    self.i2c.pyb.exit_raw_repl()
                    self.i2c.pyb.close()
                    logger.info("   ✓ Closed initial I2C connection to avoid conflicts")
                except Exception as close_e:
                    logger.warning(
                        f"   ⚠ Error closing initial I2C connection: {close_e}"
                    )

            # Initialize physical layer - it will create its own Pico connection
            self.phy_0 = Glink_phy(self.gui, None, self.jtag)
            logger.info("   ✓ Physical layer initialized")
            logger.info("   ✓ Register access methods ready")
        except Exception as e:
            logger.error(f"   ✗ Physical layer initialization failed: {e}")
            raise

    def _initialize_test_controller(self):
        """Initialize test controller (Glink_run)"""
        logger.info("Step 6: Initializing Test Controller...")
        try:
            # Initialize test controller with physical layer and GUI
            self.run_0 = Glink_run(self.phy_0, self.gui)
            logger.info("   ✓ Test controller initialized")
            logger.info("   ✓ PRTN methods ready")
        except Exception as e:
            logger.error(f"   ✗ Test controller initialization failed: {e}")
            raise

    def soft_reset(self):
        """Perform soft reset to the system"""
        logger.info("=" * 80)
        logger.info("PERFORMING SOFT RESET")
        logger.info("=" * 80)
        try:
            logger.info("   → Enabling APB access for all dies...")
            self.phy_0.resetn(abp_en=1)
            logger.info("   ✓ Soft reset completed")
            logger.info("   ✓ System is ready for testing")
            logger.info("")
        except Exception as e:
            logger.error(f"   ✗ ERROR during soft reset: {e}")
            logger.error("   ✗ This may be due to:")
            logger.error("     - Missing I2C connection to Pico")
            logger.error("     - Hardware not properly connected")
            raise

    def run_single(self):
        """
        Run single PRTN readout:
        - Runs all 4 EW_range for each block_idx
        - Combines the readout string of all block_idx for each of the 4 EW
        - Result: 4 long readouts (one per EW configuration)
        """
        logger.info("=" * 80)
        logger.info("RUNNING SINGLE PRTN READOUT")
        logger.info("=" * 80)

        # Always do soft reset at the start
        self.soft_reset()

        # Set up PRTN parameters
        self.run_0.prtn_offset = 0x40000
        self.run_0.tca_inter_reg_addr = 0x0
        self.run_0.expected_count = [31, 31, 31, 31, 31, 31, 31, 31, 13]
        self.run_0.expected_wait = 0
        self.run_0.prtn_fifo_read_address = 0x24
        self.run_0.prtn_fifo_count_address = 0x28

        block_idx_range = range(4)  # 4 blocks: S0, S1, S2, S3
        EW_range = [1, 2, 3, 4]  # 4 EW configurations
        cfg = 0x1E  # Single configuration value
        qdca_osc_bypass_cfg = [0, 0]  # QDCA configuration

        # Set up test mode (M4_D0V_D1V_mode)
        logger.info("Setting up test mode: M4_D0V_D1V_mode...")
        self.run_0.M4_D0V_D1V_mode()
        logger.info("✓ Test mode: M4_D0V_D1V_mode")
        logger.info("✓ TX Die: %d, RX Die: %d", self.run_0.tx_die, self.run_0.rx_die)

        # Check if I2C connection is working
        if not hasattr(self.phy_0, "i2c") or self.phy_0.i2c.pyb is None:
            logger.error("✗ I2C connection not available - cannot run PRTN test")
            raise Exception("I2C connection required for PRTN testing")

        # Determine which dies and groups to test based on mode
        dies_and_group_range = [{"die": 0, "group": 2}, {"die": 1, "group": 2}]

        # Store combined readouts for each EW
        ew_readouts = {}  # {EW: combined_readout_string}

        for die_and_group in dies_and_group_range:
            logger.info("")
            logger.info("-" * 80)
            logger.info(
                f"Working on Die {die_and_group['die']}, Group {die_and_group['group']}"
            )
            logger.info("-" * 80)

            # Set die and group
            self.run_0.die = die_and_group["die"]
            self.run_0.slave = self.run_0.EHOST[die_and_group["die"]][
                die_and_group["group"]
            ]
            self.phy_0.die_sel(die=self.run_0.die)

            logger.info("Enabling TCA clock to Block Controllers...")
            self.run_0.prtn_tca_clk_en()
            logger.info("TCA clock enabled")

            logger.info("Configuring global PRTN settings...")
            self.run_0.prtn_global_config()
            logger.info("Global configuration completed")

            # Enable read/measure for all blocks
            logger.info("Enabling read/measure for all blocks...")
            for block_idx in block_idx_range:
                self.run_0.prtn_tca_read_measure_en(block_idx)
            logger.info("All blocks enabled for read/measure")

            # Run readout for each EW configuration
            for EW in EW_range:
                logger.info("")
                logger.info("=== EW Configuration %d ===" % EW)

                # Configure all blocks for this EW
                logger.info(f"Configuring all blocks for EW={EW}...")
                for block_idx in block_idx_range:
                    self.run_0.prtn_config_block(block_idx, cfg, EW)
                    self.run_0.prtn_qdca_osc_cfg(
                        block_idx=block_idx,
                        include_dly_line=qdca_osc_bypass_cfg[0],
                        base_delay=cfg,
                        fine_delay=qdca_osc_bypass_cfg[1],
                    )
                logger.info(f"All blocks configured for EW={EW}")

                # Start measurement
                logger.info("Starting measurement...")
                self.run_0.prtn_reg_write(0x34, 0x1)  # broadcast_state
                val = self.run_0.prtn_reg_read(0x6C)  # became_busy
                logger.info(f"Became_busy before Start: {val}")

                # Measure command
                self.run_0.prtn_start_measure()
                self.phy_0.TX_PCS_BIST_RUN(
                    self.run_0.tx_die,
                    self.run_0.tx_group,
                    slice=self.run_0.tx_slice,
                    setv="0x1",
                )
                self.phy_0.TX_PCS_BIST_RUN(
                    self.run_0.rx_die,
                    self.run_0.rx_group,
                    slice=self.run_0.rx_slice,
                    setv="0x1",
                )
                self.phy_0.die_sel(die=self.run_0.die)
                time.sleep(0.1)

                # Stop measurement for all blocks
                logger.info("Stopping measurement for all blocks...")
                for block_idx in block_idx_range:
                    self.run_0.prtn_stop_measure(block_idx)

                self.run_0.prtn_reg_write(0x34, 0x1)  # broadcast_state

                # Read all blocks and combine their readouts
                logger.info(f"Reading data from all blocks for EW={EW}...")
                combined_readout = ""

                for block_idx in block_idx_range:
                    logger.info(f"  Reading block_idx={block_idx}...")
                    naknik = self.run_0.prtn_read_data(
                        self.run_0.expected_count, self.run_0.expected_wait, block_idx
                    )
                    combined_readout += naknik

                    logger.info(
                        f"    Block {block_idx} readout length: {len(naknik)} characters"
                    )

                    # Verify readout ended
                    val = int(self.run_0.prtn_reg_read(0x5C), 16)
                    if (val & 0x00000001) != 0x000000001:
                        logger.error(
                            f"    ⚠ Readout not ended for block_idx={block_idx}"
                        )

                    self.run_0.prtn_reg_write(0x8, 5)
                    self.run_0.prtn_reg_write(0x8, 1)

                # Store combined readout for this EW
                ew_readouts[EW] = combined_readout
                logger.info(
                    f"✓ EW={EW} combined readout length: {len(combined_readout)} characters"
                )
                logger.info(f"✓ Completed EW configuration {EW}")

        # Print all combined readouts one after the other
        logger.info("")
        logger.info("=" * 80)
        logger.info("COMBINED READOUTS (One per EW configuration)")
        logger.info("=" * 80)

        for EW in EW_range:
            logger.info("")
            logger.info("--- EW Configuration %d Combined Readout ---", EW)
            logger.info("Length: %d characters", len(ew_readouts[EW]))
            logger.info("Readout:")
            logger.info(ew_readouts[EW])
            logger.info("")

        logger.info("=" * 80)
        logger.info("SINGLE PRTN READOUT COMPLETED SUCCESSFULLY")
        logger.info("Total EW configurations: %d", len(EW_range))
        logger.info("Total blocks per EW: %d", len(block_idx_range))
        logger.info("=" * 80)

        return ew_readouts

    def cleanup(self):
        """Clean up system resources"""
        logger.info("=" * 80)
        logger.info("SYSTEM CLEANUP")
        logger.info("=" * 80)
        try:
            # Disable power supplies
            if hasattr(self.gui, "E363xA_Out_OFF"):
                self.gui.E363xA_Out_OFF()
                logger.info("✓ Power supplies disabled")

            # Close physical layer I2C connection (this is the active one)
            if (
                hasattr(self.phy_0, "i2c")
                and hasattr(self.phy_0.i2c, "pyb")
                and self.phy_0.i2c.pyb is not None
            ):
                try:
                    self.phy_0.i2c.pyb.exit_raw_repl()
                    self.phy_0.i2c.pyb.close()
                    logger.info("✓ Physical layer I2C connection closed properly")
                except Exception as close_e:
                    logger.warning(
                        f"Warning during physical layer I2C cleanup: {close_e}"
                    )
                    try:
                        self.phy_0.i2c.close()
                        logger.info("✓ Physical layer I2C connection closed (fallback)")
                    except Exception as fallback_e:
                        logger.warning(
                            f"Fallback physical layer I2C cleanup failed: {fallback_e}"
                        )

            # Also try to close the initial I2C connection if it still exists
            if (
                hasattr(self, "i2c")
                and hasattr(self.i2c, "pyb")
                and self.i2c.pyb is not None
            ):
                try:
                    self.i2c.pyb.exit_raw_repl()
                    self.i2c.pyb.close()
                    logger.info("✓ Initial I2C connection closed")
                except Exception as close_e:
                    logger.warning(f"Warning during initial I2C cleanup: {close_e}")

            logger.info("✓ System cleanup completed")
        except Exception as e:
            logger.warning(f"Warning during cleanup: {e}")


def main():
    """Main function"""
    logger.info("Starting PRTN Test Tool...")
    logger.info(f"Time: {datetime.datetime.now()}")
    logger.info("")

    test_system = None
    try:
        # Initialize test system
        test_system = PRTNTestSystem()

        # Run single readout
        ew_readouts = test_system.run_single()

        logger.info("")
        logger.info("=" * 80)
        logger.info("PRTN TEST COMPLETED SUCCESSFULLY")
        logger.info("End Time: %s", datetime.datetime.now())
        logger.info("=" * 80)

        return ew_readouts

    except KeyboardInterrupt:
        logger.info("\nOperation interrupted by user")
        return None
    except Exception as e:
        logger.error(f"PRTN test failed with error: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return None
    finally:
        if test_system:
            test_system.cleanup()


if __name__ == "__main__":
    main()
