/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * MFD core driver for Richtek RT5033
 *
 * Copyright (C) 2014 Samsung Electronics, Co., Ltd.
 * Author: Beomho Seo <beomho.seo@samsung.com>
 */

#ifndef __RT5033_PRIVATE_H__
#define __RT5033_PRIVATE_H__

enum rt5033_reg {
	RT5033_REG_CHG_STAT		= 0x00,
	RT5033_REG_CHG_CTRL1		= 0x01,
	RT5033_REG_CHG_CTRL2		= 0x02,
	RT5033_REG_DEVICE_ID		= 0x03,
	RT5033_REG_CHG_CTRL3		= 0x04,
	RT5033_REG_CHG_CTRL4		= 0x05,
	RT5033_REG_CHG_CTRL5		= 0x06,
	RT5033_REG_RT_CTRL0		= 0x07,
	RT5033_REG_CHG_RESET		= 0x08,
	/* Reserved 0x09~0x18 */
	RT5033_REG_RT_CTRL1		= 0x19,
	/* Reserved 0x1A~0x20 */
	RT5033_REG_FLED_FUNCTION1	= 0x21,
	RT5033_REG_FLED_FUNCTION2	= 0x22,
	RT5033_REG_FLED_STROBE_CTRL1	= 0x23,
	RT5033_REG_FLED_STROBE_CTRL2	= 0x24,
	RT5033_REG_FLED_CTRL1		= 0x25,
	RT5033_REG_FLED_CTRL2		= 0x26,
	RT5033_REG_FLED_CTRL3		= 0x27,
	RT5033_REG_FLED_CTRL4		= 0x28,
	RT5033_REG_FLED_CTRL5		= 0x29,
	/* Reserved 0x2A~0x40 */
	RT5033_REG_CTRL			= 0x41,
	RT5033_REG_BUCK_CTRL		= 0x42,
	RT5033_REG_LDO_CTRL		= 0x43,
	/* Reserved 0x44~0x46 */
	RT5033_REG_MANUAL_RESET_CTRL	= 0x47,
	/* Reserved 0x48~0x5F */
	RT5033_REG_CHG_IRQ1		= 0x60,
	RT5033_REG_CHG_IRQ2		= 0x61,
	RT5033_REG_CHG_IRQ3		= 0x62,
	RT5033_REG_CHG_IRQ1_CTRL	= 0x63,
	RT5033_REG_CHG_IRQ2_CTRL	= 0x64,
	RT5033_REG_CHG_IRQ3_CTRL	= 0x65,
	RT5033_REG_LED_IRQ_STAT		= 0x66,
	RT5033_REG_LED_IRQ_CTRL		= 0x67,
	RT5033_REG_PMIC_IRQ_STAT	= 0x68,
	RT5033_REG_PMIC_IRQ_CTRL	= 0x69,
	RT5033_REG_SHDN_CTRL		= 0x6A,
	RT5033_REG_OFF_EVENT		= 0x6B,

	RT5033_REG_END,
};

/* RT5033 Charger state register */
#define RT5033_CHG_STAT_MASK		0x20
#define RT5033_CHG_STAT_DISCHARGING	0x00
#define RT5033_CHG_STAT_FULL		0x10
#define RT5033_CHG_STAT_CHARGING	0x20
#define RT5033_CHG_STAT_NOT_CHARGING	0x30
#define RT5033_CHG_STAT_TYPE_MASK	0x60
#define RT5033_CHG_STAT_TYPE_PRE	0x20
#define RT5033_CHG_STAT_TYPE_FAST	0x60

/* RT5033 CHGCTRL1 register */
#define RT5033_CHGCTRL1_IAICR_MASK	0xe0
#define RT5033_CHGCTRL1_MODE_MASK	0x01

/* RT5033 CHGCTRL2 register */
#define RT5033_CHGCTRL2_CV_MASK		0xfc

/* RT5033 CHGCTRL3 register */
#define RT5033_CHGCTRL3_CFO_EN_MASK	0x40
#define RT5033_CHGCTRL3_TIMER_MASK	0x38
#define RT5033_CHGCTRL3_TIMER_EN_MASK	0x01

/* RT5033 CHGCTRL4 register */
#define RT5033_CHGCTRL4_EOC_MASK	0x07
#define RT5033_CHGCTRL4_IPREC_MASK	0x18

/* RT5033 CHGCTRL5 register */
#define RT5033_CHGCTRL5_VPREC_MASK	0x0f
#define RT5033_CHGCTRL5_ICHG_MASK	0xf0
#define RT5033_CHGCTRL5_ICHG_SHIFT	0x04
#define RT5033_CHG_MAX_CURRENT		0x0d

/* RT5033 RT CTRL1 register */
#define RT5033_RT_CTRL1_UUG_MASK	0x02
#define RT5033_RT_HZ_MASK		0x01

/* RT5033 control register */
#define RT5033_CTRL_FCCM_BUCK_MASK		0x00
#define RT5033_CTRL_BUCKOMS_MASK		0x01
#define RT5033_CTRL_LDOOMS_MASK			0x02
#define RT5033_CTRL_SLDOOMS_MASK		0x03
#define RT5033_CTRL_EN_BUCK_MASK		0x04
#define RT5033_CTRL_EN_LDO_MASK			0x05
#define RT5033_CTRL_EN_SAFE_LDO_MASK		0x06
#define RT5033_CTRL_LDO_SLEEP_MASK		0x07

/* RT5033 BUCK control register */
#define RT5033_BUCK_CTRL_MASK			0x1f

/* RT5033 LDO control register */
#define RT5033_LDO_CTRL_MASK			0x1f

/* RT5033 charger property - model, manufacturer */

#define RT5033_CHARGER_MODEL	"RT5033WSC Charger"
#define RT5033_MANUFACTURER	"Richtek Technology Corporation"

/*
 * RT5033 charger fast-charge current lmits (as in CHGCTRL1 register),
 * AICR mode limits the input current for example,
 * the AIRC 100 mode limits the input current to 100 mA.
 */
#define RT5033_AICR_100_MODE			0x20
#define RT5033_AICR_500_MODE			0x40
#define RT5033_AICR_700_MODE			0x60
#define RT5033_AICR_900_MODE			0x80
#define RT5033_AICR_1500_MODE			0xc0
#define RT5033_AICR_2000_MODE			0xe0
#define RT5033_AICR_MODE_MASK			0xe0

/* RT5033 use internal timer need to set time */
#define RT5033_FAST_CHARGE_TIMER4		0x00
#define RT5033_FAST_CHARGE_TIMER6		0x01
#define RT5033_FAST_CHARGE_TIMER8		0x02
#define RT5033_FAST_CHARGE_TIMER9		0x03
#define RT5033_FAST_CHARGE_TIMER12		0x04
#define RT5033_FAST_CHARGE_TIMER14		0x05
#define RT5033_FAST_CHARGE_TIMER16		0x06

#define RT5033_INT_TIMER_ENABLE			0x01

/* RT5033 charger termination enable mask */
#define RT5033_TE_ENABLE_MASK			0x08

/*
 * RT5033 charger opa mode. RT50300 have two opa mode charger mode
 * and boost mode for OTG
 */

#define RT5033_CHARGER_MODE			0x00
#define RT5033_BOOST_MODE			0x01

/* RT5033 charger termination enable */
#define RT5033_TE_ENABLE			0x08

/* RT5033 charger CFO enable */
#define RT5033_CFO_ENABLE			0x40

/* RT5033 charger constant charge voltage (as in CHGCTRL2 register), uV */
#define RT5033_CHARGER_CONST_VOLTAGE_LIMIT_MIN	3650000U
#define RT5033_CHARGER_CONST_VOLTAGE_STEP_NUM   25000U
#define RT5033_CHARGER_CONST_VOLTAGE_LIMIT_MAX	4400000U

/* RT5033 charger pre-charge current limits (as in CHGCTRL4 register), uA */
#define RT5033_CHARGER_PRE_CURRENT_LIMIT_MIN	350000U
#define RT5033_CHARGER_PRE_CURRENT_STEP_NUM	100000U
#define RT5033_CHARGER_PRE_CURRENT_LIMIT_MAX	650000U

/* RT5033 charger fast-charge current (as in CHGCTRL5 register), uA */
#define RT5033_CHARGER_FAST_CURRENT_MIN		700000U
#define RT5033_CHARGER_FAST_CURRENT_STEP_NUM	100000U
#define RT5033_CHARGER_FAST_CURRENT_MAX		2000000U

/*
 * RT5033 charger const-charge end of charger current (
 * as in CHGCTRL4 register), uA
 */
#define RT5033_CHARGER_EOC_MIN			150000U
#define RT5033_CHARGER_EOC_REF			300000U
#define RT5033_CHARGER_EOC_STEP_NUM1		50000U
#define RT5033_CHARGER_EOC_STEP_NUM2		100000U
#define RT5033_CHARGER_EOC_MAX			600000U

/*
 * RT5033 charger pre-charge threshold volt limits
 * (as in CHGCTRL5 register), uV
 */

#define RT5033_CHARGER_PRE_THRESHOLD_LIMIT_MIN	2300000U
#define RT5033_CHARGER_PRE_THRESHOLD_STEP_NUM	100000U
#define RT5033_CHARGER_PRE_THRESHOLD_LIMIT_MAX	3800000U

/*
 * RT5033 charger enable UUG, If UUG enable MOS auto control by H/W charger
 * circuit.
 */
#define RT5033_CHARGER_UUG_ENABLE		0x02

/* RT5033 charger High impedance mode */
#define RT5033_CHARGER_HZ_DISABLE		0x00
#define RT5033_CHARGER_HZ_ENABLE		0x01

/* RT5033 regulator BUCK output voltage uV */
#define RT5033_REGULATOR_BUCK_VOLTAGE_MIN		1000000U
#define RT5033_REGULATOR_BUCK_VOLTAGE_MAX		3000000U
#define RT5033_REGULATOR_BUCK_VOLTAGE_STEP		100000U
#define RT5033_REGULATOR_BUCK_VOLTAGE_STEP_NUM		32

/* RT5033 regulator LDO output voltage uV */
#define RT5033_REGULATOR_LDO_VOLTAGE_MIN		1200000U
#define RT5033_REGULATOR_LDO_VOLTAGE_MAX		3000000U
#define RT5033_REGULATOR_LDO_VOLTAGE_STEP		100000U
#define RT5033_REGULATOR_LDO_VOLTAGE_STEP_NUM		32

/* RT5033 regulator SAFE LDO output voltage uV */
#define RT5033_REGULATOR_SAFE_LDO_VOLTAGE		4900000U

enum rt5033_fuel_reg {
	RT5033_FUEL_REG_OCV_H		= 0x00,
	RT5033_FUEL_REG_OCV_L		= 0x01,
	RT5033_FUEL_REG_VBAT_H		= 0x02,
	RT5033_FUEL_REG_VBAT_L		= 0x03,
	RT5033_FUEL_REG_SOC_H		= 0x04,
	RT5033_FUEL_REG_SOC_L		= 0x05,
	RT5033_FUEL_REG_CTRL_H		= 0x06,
	RT5033_FUEL_REG_CTRL_L		= 0x07,
	RT5033_FUEL_REG_CRATE		= 0x08,
	RT5033_FUEL_REG_DEVICE_ID	= 0x09,
	RT5033_FUEL_REG_AVG_VOLT_H	= 0x0A,
	RT5033_FUEL_REG_AVG_VOLT_L	= 0x0B,
	RT5033_FUEL_REG_CONFIG_H	= 0x0C,
	RT5033_FUEL_REG_CONFIG_L	= 0x0D,
	/* Reserved 0x0E~0x0F */
	RT5033_FUEL_REG_IRQ_CTRL	= 0x10,
	RT5033_FUEL_REG_IRQ_FLAG	= 0x11,
	RT5033_FUEL_VMIN		= 0x12,
	RT5033_FUEL_SMIN		= 0x13,
	/* Reserved 0x14~0x1F */
	RT5033_FUEL_VGCOMP1		= 0x20,
	RT5033_FUEL_VGCOMP2		= 0x21,
	RT5033_FUEL_VGCOMP3		= 0x22,
	RT5033_FUEL_VGCOMP4		= 0x23,
	/* Reserved 0x24~0xFD */
	RT5033_FUEL_MFA_H		= 0xFE,
	RT5033_FUEL_MFA_L		= 0xFF,

	RT5033_FUEL_REG_END,
};

/* RT5033 fuel gauge battery present property */
#define RT5033_FUEL_BAT_PRESENT		0x02

/* RT5033 PMIC interrupts */
#define RT5033_PMIC_IRQ_BUCKOCP		2
#define RT5033_PMIC_IRQ_BUCKLV		3
#define RT5033_PMIC_IRQ_SAFELDOLV	4
#define RT5033_PMIC_IRQ_LDOLV		5
#define RT5033_PMIC_IRQ_OT		6
#define RT5033_PMIC_IRQ_VDDA_UV		7

#endif /* __RT5033_PRIVATE_H__ */
